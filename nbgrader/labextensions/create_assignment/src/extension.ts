import {
  Dialog,
  showDialog,
  Styling
} from '@jupyterlab/apputils';

import {
  Cell,
  ICellModel
} from '@jupyterlab/cells';

import {
  IChangedArgs
} from '@jupyterlab/coreutils';

import {
  DocumentRegistry
} from '@jupyterlab/docregistry';

import {
  INotebookModel,
  INotebookTracker,
  Notebook,
  NotebookPanel
} from '@jupyterlab/notebook';

import {
  IObservableJSON,
  IObservableList,
  IObservableMap,
  IObservableUndoableList
} from '@jupyterlab/observables';

import {
  ReadonlyPartialJSONValue
} from '@lumino/coreutils';

import {
  ISignal,
  Signal
} from '@lumino/signaling';

import {
  Panel,
  Widget
} from '@lumino/widgets';

import {
  CellModel,
  CellType,
  NBGRADER_SCHEMA_VERSION,
  ToolData
} from './model';

const CSS_CELL_HEADER = 'nbgrader-CellHeader';
const CSS_CELL_ID = 'nbgrader-CellId';
const CSS_CELL_POINTS = 'nbgrader-CellPoints';
const CSS_CELL_TYPE = 'nbgrader-CellType';
const CSS_CELL_WIDGET = 'nbgrader-CellWidget';
const CSS_CREATE_ASSIGNMENT_WIDGET = 'nbgrader-CreateAssignmentWidget';
const CSS_LOCK_BUTTON = 'nbgrader-LockButton';
const CSS_MOD_ACTIVE = 'nbgrader-mod-active';
const CSS_MOD_LOCKED = 'nbgrader-mod-locked';
const CSS_MOD_UNEDITABLE = 'nbgrader-mod-uneditable';
const CSS_NOTEBOOK_HEADER_WIDGET = 'nbgrader-NotebookHeaderWidget';
const CSS_NOTEBOOK_PANEL_WIDGET = 'nbgrader-NotebookPanelWidget';
const CSS_NOTEBOOK_POINTS = 'nbgrader-NotebookPoints';
const CSS_NOTEBOOK_WIDGET = 'nbgrader-NotebookWidget';
const CSS_TOTAL_POINTS_INPUT = 'nbgrader-TotalPointsInput';

/**
 * A widget which shows the "Create Assignment" widgets for the active notebook.
 */
export class CreateAssignmentWidget extends Panel {
  activeNotebook: NotebookPanel;
  notebookPanelWidgets = new Map<NotebookPanel, NotebookPanelWidget>();
  notebookTracker: INotebookTracker;

  constructor(tracker: INotebookTracker) {
    super();
    this.notebookTracker = tracker;
    this.addClass(CSS_CREATE_ASSIGNMENT_WIDGET);
    this.addNotebookListeners(tracker);
    this.activeNotebook = null;
  }

  addNotebookListeners(tracker: INotebookTracker) {
    tracker.widgetAdded.connect(this.getNotebookAddedListener());
    tracker.currentChanged.connect(this.getCurrentNotebookListener());
  }

  getCurrentNotebookListener(): (tracker: INotebookTracker, panel: NotebookPanel) => void {
    return (tracker: INotebookTracker, panel: NotebookPanel) => {
      if (this.activeNotebook != null) {
        const widget = this.notebookPanelWidgets.get(this.activeNotebook);
        if (widget != null) {
          widget.hide();
        }
      }
      if (panel != null) {
        const widget = this.notebookPanelWidgets.get(panel)
        if (widget != null) {
          widget.show();
        }
      }
      this.activeNotebook = panel;
    }
  }

  getNotebookAddedListener(): (tracker: INotebookTracker, panel: NotebookPanel) => void {
    return async (tracker: INotebookTracker, panel: NotebookPanel) => {
      await panel.revealed
      const notebookPanelWidget = new NotebookPanelWidget(panel);
      this.addWidget(notebookPanelWidget);
      this.notebookPanelWidgets.set(panel, notebookPanelWidget);
      notebookPanelWidget.disposed.connect(() => {
        this.notebookPanelWidgets.delete(panel);
      })
      if (tracker.currentWidget != panel) {
        notebookPanelWidget.hide();
      }
    }
  }
}

/**
 * Shows a cell's assignment data.
 */
class CellWidget extends Panel {
  cell: Cell;
  _click = new Signal<this, void>(this);
  _lock: HTMLAnchorElement;
  _task: HTMLDivElement;
  _gradeId: HTMLDivElement;
  _points: HTMLDivElement;
  _taskInput: HTMLSelectElement;
  _gradeIdInput: HTMLInputElement;
  _pointsInput: HTMLInputElement;

  constructor(cell: Cell) {
    super();
    this.cell = cell;
    this.addMetadataListener(cell);
    this.initLayout();
    this.initClickListener();
    this.initInputListeners();
    this.initMetadata(cell);
    this.addClass(CSS_CELL_WIDGET);
  }

  async addMetadataListener(cell: Cell) {
    await cell.ready;
    cell.model.metadata.changed.connect(this.getMetadataChangedHandler());
  }

  get click(): ISignal<this, void> {
    return this._click;
  }

  getCellStateChangedListener(srcPrompt: HTMLElement, destPrompt: HTMLElement):
    (model: ICellModel, changedArgs: IChangedArgs<any, any, string>) => void {
    return (model: ICellModel, changedArgs: IChangedArgs<any, any, string>) => {
      if (changedArgs.name == 'executionCount') {
        destPrompt.innerText = srcPrompt.innerText;
      }
    }
  }

  getMetadataChangedHandler(): (metadata: IObservableJSON, changedArgs:
                                IObservableMap.IChangedArgs<ReadonlyPartialJSONValue>) => void {
    return (metadata: IObservableJSON, changedArgs: IObservableMap.IChangedArgs<ReadonlyPartialJSONValue>) => {
      const nbgraderData = CellModel.getNbgraderData(metadata);
      const toolData = CellModel.newToolData(nbgraderData, this.cell.model.type);
      this.updateValues(toolData);
    }
  }

  getOnInputChanged(): () => void {
    return () => {
      const toolData = new ToolData();
      toolData.type = this._taskInput.value as CellType;
      if (!this._gradeId.classList.contains(CSS_MOD_UNEDITABLE)) {
        toolData.id = this._gradeIdInput.value;
      }
      else {
        toolData.id = 'cell-' + this._randomString(16);
        this._gradeIdInput.value = toolData.id;
      }
      if (!this._points.classList.contains(CSS_MOD_UNEDITABLE)) {
        toolData.points = this._pointsInput.valueAsNumber;
      }
      const data = CellModel.newNbgraderData(toolData);
      CellModel.setNbgraderData(data, this.cell.model.metadata);
    }
  }

  initClickListener(): void {
    this.node.addEventListener('click', () => {
      this._click.emit();
    });
  }

  initInputListeners(): void {
    this._taskInput.onchange = this.getOnInputChanged();
    this._gradeIdInput.onchange = this.getOnInputChanged();
    this._pointsInput.onchange = this.getOnInputChanged();
  }

  initLayout() {
    const bodyElement = document.createElement('div');
    const headerElement = this.newHeaderElement();
    const taskElement = this.newTaskElement();
    const idElement = this.newIdElement();
    const pointsElement = this.newPointsElement();
    const elements = [headerElement, taskElement, idElement, pointsElement];
    const fragment = document.createDocumentFragment();
    for (const element of elements) {
      fragment.appendChild(element);
    }
    bodyElement.appendChild(fragment);
    this.node.appendChild(bodyElement);
    this._lock = headerElement.getElementsByTagName('a')[0];
    this._task = taskElement;
    this._gradeId = idElement;
    this._points = pointsElement;
    this._taskInput = taskElement.getElementsByTagName('select')[0];
    this._gradeIdInput = idElement.getElementsByTagName('input')[0];
    this._pointsInput = pointsElement.getElementsByTagName('input')[0];
  }

  async initMetadata(cell: Cell) {
    await cell.ready
    if (cell.model == null) {
      return;
    }
    const nbgraderData = CellModel.getNbgraderData(cell.model.metadata);
    const toolData = CellModel.newToolData(nbgraderData, this.cell.model.type);
    this.updateValues(toolData);
  }

  newHeaderElement(): HTMLDivElement {
    const element = document.createElement('div');
    element.className = CSS_CELL_HEADER;
    const promptNode =  this.cell.promptNode.cloneNode(true) as HTMLElement;
    element.appendChild(promptNode);
    this.cell.model.stateChanged.connect(this.getCellStateChangedListener(
      this.cell.promptNode, promptNode));
    const lockElement = document.createElement('a');
    lockElement.className = CSS_LOCK_BUTTON;
    const listElement = document.createElement('li');
    listElement.className = 'fa fa-lock';
    listElement.title = 'Student changes will be overwritten';
    lockElement.appendChild(listElement);
    element.appendChild(lockElement);
    return element;
  }

  newIdElement(): HTMLDivElement {
    const element = document.createElement('div');
    element.className = CSS_CELL_ID;
    const label = document.createElement('label');
    label.textContent = 'ID: ';
    const input = document.createElement('input');
    input.type = 'text';
    label.appendChild(input);
    element.appendChild(label);
    return element;
  }

  newPointsElement(): HTMLDivElement {
    const element = document.createElement('div');
    element.className = CSS_CELL_POINTS;
    const label = document.createElement('label');
    label.textContent = 'Points: ';
    const input = document.createElement('input');
    input.type = 'number';
    input.min = '0';
    label.appendChild(input);
    element.appendChild(label);
    return element;
  }

  newTaskElement(): HTMLDivElement {
    const element = document.createElement('div');
    element.className = CSS_CELL_TYPE;
    const label = document.createElement('label');
    label.textContent = 'Type: ';
    const select = document.createElement('select');
    const options = new Map<string, string>([
      ['', '-'],
      ['manual', 'Manually graded answer'],
      ['task', 'Manually graded task'],
      ['solution', 'Autograded answer'],
      ['tests', 'Autograded task'],
      ['readonly', 'Read-only']
    ]);
    if (this.cell.model.type !== 'code') {
      options.delete('solution');
      options.delete('tests');
    }
    const fragment = document.createDocumentFragment();
    for (const optionEntry of options.entries()) {
      const option = document.createElement('option');
      option.value = optionEntry[0];
      option.innerHTML = optionEntry[1];
      fragment.appendChild(option);
    }
    select.appendChild(fragment);
    const selectWrap = Styling.wrapSelect(select);
    label.appendChild(selectWrap);
    element.appendChild(label);
    return element;
  }

  setActive(active: boolean) {
    if (active) {
      this.addClass(CSS_MOD_ACTIVE);
    }
    else {
      this.removeClass(CSS_MOD_ACTIVE);
    }
  }

  setGradeId(value: string) {
    this._gradeIdInput.value = value;
  }

  setElementEditable(element: HTMLElement, visible: boolean) {
    if (visible) {
      element.classList.remove(CSS_MOD_UNEDITABLE);
    }
    else {
      element.classList.add(CSS_MOD_UNEDITABLE);
    }
  }

  setGradeIdEditable(visible: boolean) {
    this.setElementEditable(this._gradeId, visible);
  }

  setPoints(value: number) {
    this._pointsInput.value = value.toString();
  }

  setPointsEditable(visible: boolean) {
    this.setElementEditable(this._points, visible);
  }

  setTask(value: string) {
    this._taskInput.value = value;
  }

  updateValues(data: ToolData) {
    this.setTask(data.type);
    if (data.id == null) {
      this.setGradeIdEditable(false);
      this.setGradeId('');
    }
    else {
      this.setGradeId(data.id);
      this.setGradeIdEditable(true);
    }
    if (data.points == null) {
      this.setPointsEditable(false);
      this.setPoints(0);
    }
    else {
      this.setPoints(data.points);
      this.setPointsEditable(true);
    }
    if (data.locked) {
      this._lock.classList.add(CSS_MOD_LOCKED);
    }
    else {
      this._lock.classList.remove(CSS_MOD_LOCKED);
    }
  }

  private _randomString(length: number): string {
    var result = '';
    var chars = 'abcdef0123456789';
    var i;
    for (i = 0; i < length; i++) {
      result += chars[Math.floor(Math.random() * chars.length)];
    }
    return result;
  }
}

/**
 * The header of a notebook's Create Assignment widget.
 *
 * Displays the total points in the notebook.
 */
class NotebookHeaderWidget extends Widget {
  _pointsInput: HTMLInputElement;

  constructor() {
    super();
    this.addClass(CSS_NOTEBOOK_HEADER_WIDGET);
    this.initLayout();
  }

  initLayout(): void {
    const totalPoints = this.newTotalPointsElement();
    this.node.appendChild(totalPoints);
    this._pointsInput = totalPoints.getElementsByTagName('input')[0];
  }

  newTotalPointsElement(): HTMLDivElement {
    const element = document.createElement('div');
    element.className = CSS_NOTEBOOK_POINTS;
    const label = document.createElement('label');
    label.innerText = 'Total points:';
    const input = document.createElement('input');
    input.className = CSS_TOTAL_POINTS_INPUT;
    input.type = 'number';
    input.disabled = true;
    label.appendChild(input);
    element.appendChild(label);
    return element;
  }

  set totalPoints(points: number) {
    if (this._pointsInput != null) {
      this._pointsInput.value = points.toString();
    }
  }
}

/**
 * Contains a list of {@link CellWidget}s for a notebook.
 */
class NotebookWidget extends Panel {
  _activeCell = null as Cell;
  _notebookPanel: NotebookPanel;
  cellMetadataChanged = new Signal<this, CellWidget>(this);
  cellWidgets = new Map<Cell, CellWidget>();

  constructor(panel: NotebookPanel) {
    super();
    this._activeCell = panel.content.activeCell;
    this._notebookPanel = panel;
    this.addClass(CSS_NOTEBOOK_WIDGET);
    this.addCellListener(panel);
    this.addCellListListener(panel);
    this.initCellWidgets(panel.content);
    this.validateSchemaVersion();
    this.addValidateIdsListener();
    panel.disposed.connect(this.getNotebookDisposedListener());
  }

  addCellListener(panel: NotebookPanel) {
    panel.content.activeCellChanged.connect(this.getActiveCellListener());
  }

  addCellListListener(panel: NotebookPanel) {
    panel.model.cells.changed.connect(
      (sender: IObservableUndoableList<ICellModel>,
       args: IObservableList.IChangedArgs<ICellModel>) => {
         switch (args.type) {
           case 'add': {
             const cell = this._findCellInArray(args.newValues[0], panel.content.widgets);
             this.addCellWidget(cell, args.newIndex);
             break;
           }
           case 'move': {
             const cell = panel.content.widgets[args.newIndex];
             this.moveCellWidget(cell, args.newIndex);
             break;
           }
           case 'remove': {
             const cell = this._findDeadCell(this.cellWidgets.keys());
             if (cell != null) {
               this.removeCellWidget(cell);
             }
             else {
               console.warn('nbgrader: Unable to find newly deleted cell.');
             }
             break;
           }
           case 'set': {
             // Existing notebook cell changed. Update the corresponding widget.
             const oldCell = this._findDeadCell(this.cellWidgets.keys());
             if (oldCell != null) {
               const newCell = this._findCellInArray(args.newValues[0],
                                                     panel.content.widgets);
               this.cellWidgets.get(oldCell).dispose();
               this.cellWidgets.delete(oldCell);
               const cellWidget = this.addCellWidget(newCell, args.newIndex);
               if (this._activeCell === newCell) {
                 cellWidget.setActive(this._activeCell === newCell);
                 this._scrollIntoViewNearest(cellWidget);
               }
             }
           }
         }
    });
  }

  addCellWidget(cell: Cell, index = undefined as number): CellWidget {
    const cellWidget = new CellWidget(cell);
    this.cellWidgets.set(cell, cellWidget);
    if (index == null) {
      this.addWidget(cellWidget);
    }
    else {
      this.insertWidget(index, cellWidget);
    }
    cellWidget.click.connect(this.getActiveCellWidgetListener());
    cell.model.metadata.changed.connect(this.getMetadataChangedHandler(cellWidget));
    return cellWidget;
  }

  addValidateIdsListener(): void {
    this._notebookPanel.context.saveState.connect(
      (context: DocumentRegistry.IContext<INotebookModel>,
       args: DocumentRegistry.SaveState) => {
         if (args != 'started') {
           return;
         }
         this.validateIds();
      });
  }

  _findCellInArray(model: ICellModel, cells: readonly Cell[]): Cell {
    return cells.find(
      (value: Cell, index: number, obj: readonly Cell[]) => {
        return value.model === model;
      });
  }

  _findDeadCell(cells: IterableIterator<Cell>): Cell {
    for (const cell of cells) {
      if (cell.model == null) {
        return cell;
      }
    }
    return undefined;
  }

  getActiveCellListener(): (notebook: Notebook, cell: Cell) => void {
    return (notebook: Notebook, cell: Cell) => {
      if (this._activeCell != null) {
        const activeWidget = this.cellWidgets.get(this._activeCell);
        if (activeWidget != null) {
          activeWidget.setActive(false);
        }
      }
      if (cell != null) {
        const activeWidget = this.cellWidgets.get(cell);
        if (activeWidget != null) {
          activeWidget.setActive(true);
          this._scrollIntoViewNearest(activeWidget);
        }
      }
      this._activeCell = cell;
    }
  }

  getActiveCellWidgetListener():
      (cellWidget: CellWidget) => void {
    return (cellWidget: CellWidget) => {
      const i = this._notebookPanel.content.widgets.indexOf(cellWidget.cell);
      this._notebookPanel.content.activeCellIndex = i;
    }
  }

  getNotebookDisposedListener(): (panel: NotebookPanel) => void {
    return (panel: NotebookPanel) => {
      this.dispose();
    }
  }

  initCellWidgets(notebook: Notebook) {
    for (const cell of notebook.widgets) {
      const cellWidget = this.addCellWidget(cell);
      cellWidget.setActive(notebook.activeCell === cell);
    }
  }

  getMetadataChangedHandler(cellWidget: CellWidget):
      (metadata: IObservableJSON,
       args: IObservableMap.IChangedArgs<ReadonlyPartialJSONValue>) => void {
    return (metadata: IObservableJSON,
            args: IObservableMap.IChangedArgs<ReadonlyPartialJSONValue>) => {
      this.cellMetadataChanged.emit(cellWidget);
    }
  }

  moveCellWidget(cell: Cell, index: number) {
    const cellWidget = this.cellWidgets.get(cell);
    this.insertWidget(index, cellWidget);
  }

  get notebookPanel(): NotebookPanel {
    return this._notebookPanel;
  }

  removeCellWidget(cell: Cell) {
    const cellWidget = this.cellWidgets.get(cell);
    if (cellWidget == null) {
      return;
    }
    this.cellWidgets.delete(cell);
    cellWidget.dispose();
  }

  validateIds(): void {
    const set = new Set<string>();
    const valid = /^[a-zA-Z0-9_\-]+$/;
    const iter = this._notebookPanel.model.cells.iter();
    for (let cellModel = iter.next(); cellModel != null;
         cellModel = iter.next()) {
      const data = CellModel.getNbgraderData(cellModel.metadata)
      const id = data == null ? null : data.grade_id;
      if (!valid.test(id)) {
        this.warnInvalidId(true, false, id);
        return;
      }
      else if (set.has(id)) {
        this.warnInvalidId(false, true, id);
        return;
      }
      else {
        set.add(id);
      }
    }
  }

  validateSchemaVersion(): void {
    const iter = this._notebookPanel.model.cells.iter();
    for (let cellModel = iter.next(); cellModel != null;
         cellModel = iter.next()) {
      const data = CellModel.getNbgraderData(cellModel.metadata)
      const version = data == null ? null : data.schema_version;
      if (version != null && version < NBGRADER_SCHEMA_VERSION) {
        this.warnSchemaVersion(version);
        return;
      }
    }
  }

  warnInvalidId(badFormat: boolean, duplicateId: boolean, id: string) {
    const options = {
      buttons: [Dialog.okButton()],
      title: undefined as string,
      body: undefined as string
    };
    if (badFormat) {
      options.title = 'Invalid nbgrader cell ID';
      options.body = 'At least one cell has an invalid nbgrader ID. Cell IDs ' +
          'must contain at least one character, and may only contain ' +
          'letters, numbers, hyphens, and/or underscores.';
      showDialog(options);
      return;
    }
    else if (duplicateId) {
      options.title = 'Duplicate nbgrader cell ID';
      options.body = `The nbgrader ID "${id}" has been used for more than ` +
          `one cell. Please make sure all grade cells have unique ids.`;
      showDialog(options);
      return;
    }
  }

  warnSchemaVersion(schemaVersion: number): void {
    const version = schemaVersion.toString();
    const notebookPath = this._notebookPanel.sessionContext.path;
    const body = document.createElement('p');
    const code = document.createElement('code');
    const bodyWidget = new Widget({node: body});
    const options = {
      title: 'Outdated schema version',
      body: bodyWidget,
      buttons: [Dialog.okButton()]
    }
    body.innerText =
        `At least one cell has an old version (${version}) of the ` +
        'nbgrader metadata. Please back up this notebook and then ' +
        'update the metadata on the command ' +
        'line using the following command: ';
    code.innerText = `nbgrader update ${notebookPath}`;
    body.appendChild(code);
    showDialog(options);
  }

  private _scrollIntoViewNearest(widget: CellWidget) {
    const parentTop = this.node.scrollTop;
    const parentBottom = parentTop + this.node.clientHeight;
    const widgetTop = widget.node.offsetTop;
    const widgetBottom = widgetTop + widget.node.clientHeight;
    if (widgetTop < parentTop) {
      widget.node.scrollIntoView(true);
    }
    else if (widgetBottom > parentBottom) {
      if (widgetBottom - widgetTop > parentBottom - parentTop) {
        widget.node.scrollIntoView(true);
      }
      else {
        widget.node.scrollIntoView(false);
      }
    }
  }
}

/**
 * Contains a notebook's "Create Assignment" UI.
 */
class NotebookPanelWidget extends Panel {
  _notebookHeaderWidget: NotebookHeaderWidget;
  _notebookWidget: NotebookWidget;

  constructor(panel: NotebookPanel) {
    super();
    this.addClass(CSS_NOTEBOOK_PANEL_WIDGET);
    this.initLayout(panel);
    this.setUpTotalPoints();
  }

  calcTotalPoints(): number {
    let totalPoints = 0;
    const iter = this._notebookWidget.notebookPanel.model.cells.iter();
    for (let cellModel = iter.next(); cellModel != null;
         cellModel = iter.next()) {
      const data = CellModel.getNbgraderData(cellModel.metadata);
      const points = (data == null || data.points == null) ? 0 : data.points;
      totalPoints += points;
    }
    return totalPoints;
  }

  initLayout(panel: NotebookPanel): void {
    this._notebookHeaderWidget = new NotebookHeaderWidget();
    this._notebookWidget = new NotebookWidget(panel);
    this.addWidget(this._notebookHeaderWidget);
    this.addWidget(this._notebookWidget);
  }

  setUpTotalPoints(): void {
    this._notebookHeaderWidget.totalPoints = this.calcTotalPoints();
    this._notebookWidget.notebookPanel.model.cells.changed.connect(
      (cellModels: IObservableUndoableList<ICellModel>,
       args: IObservableList.IChangedArgs<ICellModel>) => {
         if (args.type != 'move') {
           this._notebookHeaderWidget.totalPoints = this.calcTotalPoints();
         }
       });
    this._notebookWidget.cellMetadataChanged.connect(
       (notebookWidget: NotebookWidget, cellWidget: CellWidget) => {
         this._notebookHeaderWidget.totalPoints = this.calcTotalPoints();
       });
  }
}
