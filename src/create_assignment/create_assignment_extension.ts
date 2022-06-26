import { ILabShell, LabShell } from '@jupyterlab/application';
import {
  Dialog,
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

import { each } from '@lumino/algorithm';

import {
  ReadonlyPartialJSONValue
} from '@lumino/coreutils';

import {
  Message
} from '@lumino/messaging';

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
} from './create_assignment_model';

const CSS_CELL_HEADER = 'nbgrader-CellHeader';
const CSS_CELL_ID = 'nbgrader-CellId';
const CSS_CELL_POINTS = 'nbgrader-CellPoints';
const CSS_CELL_TYPE = 'nbgrader-CellType';
const CSS_CELL_WIDGET = 'nbgrader-CellWidget';
const CSS_CREATE_ASSIGNMENT_WIDGET = 'nbgrader-CreateAssignmentWidget';
const CSS_LOCK_BUTTON = 'nbgrader-LockButton';
const CSS_MOD_ACTIVE = 'nbgrader-mod-active';
const CSS_MOD_HIGHLIGHT = 'nbgrader-mod-highlight';
const CSS_MOD_LOCKED = 'nbgrader-mod-locked';
const CSS_MOD_UNEDITABLE = 'nbgrader-mod-uneditable';
const CSS_NOTEBOOK_HEADER_WIDGET = 'nbgrader-NotebookHeaderWidget';
const CSS_NOTEBOOK_PANEL_WIDGET = 'nbgrader-NotebookPanelWidget';
const CSS_NOTEBOOK_POINTS = 'nbgrader-NotebookPoints';
const CSS_NOTEBOOK_WIDGET = 'nbgrader-NotebookWidget';
const CSS_TOTAL_POINTS_INPUT = 'nbgrader-TotalPointsInput';
const CSS_ERROR_DIALOG = 'nbgrader-ErrorDialog'


function showErrorDialog<T>(options: Partial<Dialog.IOptions<T>> = {}): Promise<Dialog.IResult<T>> {
  const dialog = new Dialog(options);
  dialog.addClass(CSS_ERROR_DIALOG);
  return dialog.launch();
}

/**
 * A widget which shows the "Create Assignment" widgets for the active notebook.
 */
export class CreateAssignmentWidget extends Panel {
  private activeNotebook: NotebookPanel;
  private currentNotebookListener: (tracker: INotebookTracker,
                                    panel: NotebookPanel) => void;
  private mainAreaListener: (shell: LabShell, changed: ILabShell.IChangedArgs) => void;
  private notebookPanelWidgets = new Map<NotebookPanel, NotebookPanelWidget>();
  private notebookTracker: INotebookTracker;
  private shell: ILabShell;

  constructor(tracker: INotebookTracker, shell: ILabShell) {
    super();
    this.addClass(CSS_CREATE_ASSIGNMENT_WIDGET);
    this.addNotebookListeners(tracker);
    this.addMainAreaActiveListener(shell);
    this.activeNotebook = null;
    this.notebookTracker = tracker;
    this.shell = shell;
  }

  private addNotebookListeners(tracker: INotebookTracker): void {
    this.currentNotebookListener = this.getCurrentNotebookListener();
    tracker.currentChanged.connect(this.currentNotebookListener);
  }

  private addMainAreaActiveListener(shell: LabShell): void {
    this.mainAreaListener = this.getMainAreaActiveListener();
    shell.currentChanged.connect(this.mainAreaListener);
  }

  private async addNotebookWidget(
    tracker: INotebookTracker,
    panel: NotebookPanel) {

      if (panel === null) return;

      await panel.revealed;
      const notebookPanelWidget = new NotebookPanelWidget(panel);
      this.addWidget(notebookPanelWidget);
      this.notebookPanelWidgets.set(panel, notebookPanelWidget);

      panel.disposed.connect(() => {
        notebookPanelWidget.dispose();
      });
      notebookPanelWidget.disposed.connect(() => {
        this.notebookPanelWidgets.delete(panel);
      });
      if (tracker.currentWidget != panel) {
        notebookPanelWidget.hide();
      }
      return panel.revealed;
  }

  dispose(): void {
    if (this.isDisposed) {
      return;
    }
    if (this.notebookPanelWidgets != null) {
      for (const widget of this.notebookPanelWidgets) {
        widget[1].dispose();
      }
    }
    if (this.notebookTracker != null) {
      this.removeNotebookListeners(this.notebookTracker);
    }
    this.activeNotebook = null;
    this.notebookPanelWidgets = null;
    this.notebookTracker = null;
    super.dispose();
  }

  private getCurrentNotebookListener(): (tracker: INotebookTracker,
                                         panel: NotebookPanel) => void {
    return async (tracker: INotebookTracker, panel: NotebookPanel) => {
      if (this.activeNotebook != null) {
        const widget = this.notebookPanelWidgets.get(this.activeNotebook);
        if (widget != null) {
          widget.hide();
        }
      }
      if (panel != null) {
        if (this.isVisible && this.notebookPanelWidgets.get(panel) == null) {
          await this.addNotebookWidget(tracker, panel);
        }
        const widget = this.notebookPanelWidgets.get(panel);
        if (widget != null) {
          widget.show();
        }
      }
      this.activeNotebook = panel;
    }
  }

  /*
   * The listener on the main area tab change
   * to collapse create_assignment widget if the current tab is not a Notebook
   */
  private getMainAreaActiveListener(): (
    shell: ILabShell,
    changed: ILabShell.IChangedArgs) => void {
      return async (shell: ILabShell, changed: ILabShell.IChangedArgs) => {
        if ( !(changed.newValue instanceof NotebookPanel) && this.isVisible) {
          this.hideRightPanel();
        }
    }
  }

  protected onBeforeShow(msg: Message): void {
    super.onBeforeShow(msg);
    if (this.activeNotebook != null){
      const notebookWidget = this.notebookPanelWidgets.get(this.activeNotebook);
      if (notebookWidget == null) {
        this.addNotebookWidget(this.notebookTracker, this.activeNotebook);
      }
      else {
        notebookWidget.show();
      }
    }
  }

  /*
   * Check if the widget must be visible :
   *  -> is there an active Notebook visible in main panel ?
   */
  protected onAfterShow(): void {
    const widgets = this.shell.widgets('main');
    if (this.activeNotebook == null){
      this.hideRightPanel();
    }
    else {
      each(widgets, w => {
        if (w.title == this.activeNotebook.title) {
          if (!w.isVisible) this.hideRightPanel();
          else w.activate();
        }
      });
    }
  }

  private hideRightPanel(): void {
    this.shell.collapseRight();
  }

  private removeNotebookListeners(tracker: INotebookTracker): void {
    tracker.currentChanged.disconnect(this.currentNotebookListener);
    this.currentNotebookListener = null;
  }
}

/**
 * Shows a cell's assignment data.
 */
class CellWidget extends Panel {
  private _cell: Cell;
  private _click = new Signal<this, void>(this);
  private metadataChangedHandler:
      (metadata: IObservableJSON,
       changedArgs: IObservableMap.IChangedArgs<ReadonlyPartialJSONValue>) =>
      void;
  private onclick: (this: HTMLElement, ev: MouseEvent) => any;
  private lock: HTMLAnchorElement;
  private gradeId: HTMLDivElement;
  private points: HTMLDivElement;
  private taskInput: HTMLSelectElement;
  private gradeIdInput: HTMLInputElement;
  private pointsInput: HTMLInputElement;

  constructor(cell: Cell) {
    super();
    this._cell = cell;
    this.addMetadataListener(cell);
    this.initLayout();
    this.initClickListener();
    this.initInputListeners();
    this.initMetadata(cell);
    this.addClass(CSS_CELL_WIDGET);
  }

  private async addMetadataListener(cell: Cell) {
    await cell.ready;
    this.metadataChangedHandler = this.getMetadataChangedHandler();
    cell.model.metadata.changed.connect(this.metadataChangedHandler);
  }

  /**
   * The notebook cell associated with this widget.
   */
  get cell(): Cell {
    return this._cell;
  }

  private cleanNbgraderData(cell: Cell): void {
    CellModel.cleanNbgraderData(cell.model.metadata, cell.model.type);
  }

  /**
   * A signal for when this widget receives a click event.
   */
  get click(): ISignal<this, void> {
    return this._click;
  }

  dispose(): void {
    if (this.isDisposed) {
      return;
    }
    if (this.metadataChangedHandler != null) {
      this.cell?.model?.metadata?.changed?.disconnect(
          this.metadataChangedHandler);
    }
    if (this.onclick != null) {
      this.node?.removeEventListener('click', this.onclick);
    }
    if (this.taskInput != null) {
      this.taskInput.onchange = null;
    }
    if (this.gradeIdInput != null) {
      this.gradeIdInput.onchange = null;
    }
    if (this.pointsInput != null) {
      this.pointsInput.onchange = null;
    }
    this._cell = null;
    this._click = null;
    this.metadataChangedHandler = null;
    this.onclick = null;
    this.lock = null;
    this.gradeId = null;
    this.points = null;
    this.taskInput = null;
    this.gradeIdInput = null;
    this.pointsInput = null;
    super.dispose();
  }

  private getCellStateChangedListener(
      srcPrompt: HTMLElement, destPrompt: HTMLElement):
      (model: ICellModel, changedArgs: IChangedArgs<any, any, string>) => void {
    return (model: ICellModel, changedArgs: IChangedArgs<any, any, string>) => {
      if (changedArgs.name == 'executionCount') {
        destPrompt.innerText = srcPrompt.innerText;
      }
    }
  }

  private getMetadataChangedHandler():
      (metadata: IObservableJSON,
       changedArgs: IObservableMap.IChangedArgs<ReadonlyPartialJSONValue>) =>
      void {
    return (metadata: IObservableJSON, changedArgs:
            IObservableMap.IChangedArgs<ReadonlyPartialJSONValue>) => {
      const nbgraderData = CellModel.getNbgraderData(metadata);
      const toolData = CellModel.newToolData(nbgraderData, this.cell.model.type);
      this.updateValues(toolData);
    }
  }

  private getOnInputChanged(): () => void {
    return () => {
      const toolData = new ToolData();
      toolData.type = this.taskInput.value as CellType;
      if (!this.gradeId.classList.contains(CSS_MOD_UNEDITABLE)) {
        toolData.id = this.gradeIdInput.value;
      }
      else {
        const nbgraderData = CellModel.getNbgraderData(
            this.cell.model.metadata);
        if (nbgraderData?.grade_id == null) {
          toolData.id = 'cell-' + this.randomString(16);
        }
        else {
          toolData.id = nbgraderData.grade_id;
        }
        this.gradeIdInput.value = toolData.id;
      }
      if (!this.points.classList.contains(CSS_MOD_UNEDITABLE)) {
        toolData.points = this.pointsInput.valueAsNumber;
      }
      const data = CellModel.newNbgraderData(toolData);
      CellModel.setNbgraderData(data, this.cell.model.metadata);
    }
  }

  private getOnTaskInputChanged(): () => void {
    const onInputChanged = this.getOnInputChanged();
    return () => {
      onInputChanged();
      this.updateDisplayClass();
    }
  }

  private initClickListener(): void {
    this.onclick = () => {
      this._click.emit();
    };
    this.node.addEventListener('click', this.onclick);
  }

  private initInputListeners(): void {
    this.taskInput.onchange = this.getOnTaskInputChanged();
    this.gradeIdInput.onchange = this.getOnInputChanged();
    this.pointsInput.onchange = this.getOnInputChanged();
  }

  private initLayout(): void {
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
    this.lock = headerElement.getElementsByTagName('a')[0];
    this.gradeId = idElement;
    this.points = pointsElement;
    this.taskInput = taskElement.getElementsByTagName('select')[0];
    this.gradeIdInput = idElement.getElementsByTagName('input')[0];
    this.pointsInput = pointsElement.getElementsByTagName('input')[0];
  }

  private async initMetadata(cell: Cell) {
    await cell.ready
    if (cell.model == null) {
      return;
    }
    this.cleanNbgraderData(cell);
    const nbgraderData = CellModel.getNbgraderData(cell.model.metadata);
    const toolData = CellModel.newToolData(nbgraderData, this.cell.model.type);
    CellModel.clearCellType(cell.model.metadata);
    this.updateDisplayClass();
    this.updateValues(toolData);
  }

  private newHeaderElement(): HTMLDivElement {
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

  private newIdElement(): HTMLDivElement {
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

  private newPointsElement(): HTMLDivElement {
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

  private newTaskElement(): HTMLDivElement {
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
      ['tests', 'Autograded tests'],
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

  private randomString(length: number): string {
    var result = '';
    var chars = 'abcdef0123456789';
    var i;
    for (i = 0; i < length; i++) {
      result += chars[Math.floor(Math.random() * chars.length)];
    }
    return result;
  }

  /**
   * Sets this cell as active/focused.
   */
  setActive(active: boolean): void {
    if (active) {
      this.addClass(CSS_MOD_ACTIVE);
    }
    else {
      this.removeClass(CSS_MOD_ACTIVE);
    }
  }

  private setGradeId(value: string): void {
    this.gradeIdInput.value = value;
  }

  private setElementEditable(element: HTMLElement, visible: boolean): void {
    if (visible) {
      element.classList.remove(CSS_MOD_UNEDITABLE);
    }
    else {
      element.classList.add(CSS_MOD_UNEDITABLE);
    }
  }

  private setGradeIdEditable(visible: boolean): void {
    this.setElementEditable(this.gradeId, visible);
  }

  private setPoints(value: number): void {
    this.pointsInput.value = value.toString();
  }

  private setPointsEditable(visible: boolean): void {
    this.setElementEditable(this.points, visible);
  }

  private setTask(value: string): void {
    this.taskInput.value = value;
  }

  private updateDisplayClass(): void {
    const data = CellModel.getNbgraderData(this.cell.model.metadata);
    if (CellModel.isRelevantToNbgrader(data)) {
      this.addClass(CSS_MOD_HIGHLIGHT);
    }
    else {
      this.removeClass(CSS_MOD_HIGHLIGHT);
    }
  }

  private updateValues(data: ToolData): void {
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
      this.lock.classList.add(CSS_MOD_LOCKED);
    }
    else {
      this.lock.classList.remove(CSS_MOD_LOCKED);
    }
  }
}

/**
 * The header of a notebook's Create Assignment widget.
 *
 * Displays the total points in the notebook.
 */
class NotebookHeaderWidget extends Widget {
  private pointsInput: HTMLInputElement;

  constructor() {
    super();
    this.addClass(CSS_NOTEBOOK_HEADER_WIDGET);
    this.initLayout();
  }

  dispose(): void {
    if (this.isDisposed) {
      return;
    }
    this.pointsInput = null;
    super.dispose();
  }

  private initLayout(): void {
    const totalPoints = this.newTotalPointsElement();
    this.node.appendChild(totalPoints);
    this.pointsInput = totalPoints.getElementsByTagName('input')[0];
  }

  private newTotalPointsElement(): HTMLDivElement {
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

  /**
   * The total points in the notebook.
   */
  set totalPoints(points: number) {
    if (this.pointsInput != null) {
      this.pointsInput.value = points.toString();
    }
  }
}

/**
 * Contains a list of {@link CellWidget}s for a notebook.
 */
class NotebookWidget extends Panel {
  private activeCell = null as Cell;
  private activeCellWidgetListener: (cellWidget: CellWidget) => void;
  private cellListener: (notebook: Notebook, cell: Cell) => void;
  private cellListListener:
      (sender: IObservableUndoableList<ICellModel>,
       args: IObservableList.IChangedArgs<ICellModel>) => void;
  private _cellMetadataChanged = new Signal<this, CellWidget>(this);
  private cellWidgets = new Map<Cell, CellWidget>();
  private metadataChangedHandlers = new Map<
      CellWidget,
      (metadata: IObservableJSON,
       args: IObservableMap.IChangedArgs<ReadonlyPartialJSONValue>) => void>();
  private notebookDisposedListener: (panel: NotebookPanel) => void;
  private _notebookPanel: NotebookPanel;
  private validateIdsListener:
      (context: DocumentRegistry.IContext<INotebookModel>,
       args: DocumentRegistry.SaveState) => void;

  constructor(panel: NotebookPanel) {
    super();
    this.activeCell = panel.content.activeCell;
    this.activeCellWidgetListener = this.getActiveCellWidgetListener();
    this._notebookPanel = panel;
    this.addClass(CSS_NOTEBOOK_WIDGET);
    this.addCellListener(panel);
    this.addCellListListener(panel);
    this.initCellWidgets(panel.content);
    this.validateSchemaVersion();
    this.addValidateIdsListener();
    this.addNotebookDisposedListener(panel);
  }

  private addCellListener(panel: NotebookPanel) {
    this.cellListener = this.getActiveCellListener();
    panel.content.activeCellChanged.connect(this.cellListener);
  }

  private addCellListListener(panel: NotebookPanel) {
    this.cellListListener =
      (sender: IObservableUndoableList<ICellModel>,
       args: IObservableList.IChangedArgs<ICellModel>) => {
         switch (args.type) {
           case 'add': {
             const cell = this.findCellInArray(args.newValues[0],
                                                panel.content.widgets);
             this.addCellWidget(cell, args.newIndex);
             break;
           }
           case 'move': {
             const cell = panel.content.widgets[args.newIndex];
             this.moveCellWidget(cell, args.newIndex);
             break;
           }
           case 'remove': {
             const cell = this.findDeadCell(this.cellWidgets.keys());
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
             const oldCell = this.findDeadCell(this.cellWidgets.keys());
             if (oldCell != null) {
               const newCell = this.findCellInArray(args.newValues[0],
                                                     panel.content.widgets);
               this.cellWidgets.get(oldCell).dispose();
               this.cellWidgets.delete(oldCell);
               const cellWidget = this.addCellWidget(newCell, args.newIndex);
               if (this.activeCell === newCell) {
                 cellWidget.setActive(this.activeCell === newCell);
                 this.scrollIntoViewNearest(cellWidget);
               }
             }
           }
         }
    };
    panel.model.cells.changed.connect(this.cellListListener);
  }

  private addCellWidget(cell: Cell, index = undefined as number): CellWidget {
    const cellWidget = new CellWidget(cell);
    this.cellWidgets.set(cell, cellWidget);
    if (index == null) {
      this.addWidget(cellWidget);
    }
    else {
      this.insertWidget(index, cellWidget);
    }
    cellWidget.click.connect(this.activeCellWidgetListener);
    const metadataChangedHandler = this.getMetadataChangedHandler(cellWidget);
    cell.model.metadata.changed.connect(metadataChangedHandler);
    this.metadataChangedHandlers.set(cellWidget, metadataChangedHandler);
    return cellWidget;
  }

  private addNotebookDisposedListener(panel: NotebookPanel): void {
    this.notebookDisposedListener = this.getNotebookDisposedListener();
    panel.disposed.connect(this.notebookDisposedListener);
  }

  private addValidateIdsListener(): void {
    this.validateIdsListener =
      (context: DocumentRegistry.IContext<INotebookModel>,
       args: DocumentRegistry.SaveState) => {
         if (args != 'started') {
           return;
         }
         this.validateIds();
      };
    this.notebookPanel.context.saveState.connect(this.validateIdsListener);
  }

  /**
   * A signal which is evoked when one of the cell's metadata changes.
   */
  get cellMetadataChanged(): Signal<this, CellWidget> {
    return this._cellMetadataChanged;
  }

  dispose(): void {
    if (this.isDisposed) {
      return;
    }
    if (this.cellWidgets != null) {
      for (const widgets of this.cellWidgets) {
        this.removeCellWidget(widgets[0]);
      }
    }
    if (this.cellListener != null) {
      this.notebookPanel?.content?.activeCellChanged?.disconnect(
          this.cellListener);
    }
    if (this.cellListListener != null) {
      this.notebookPanel?.model?.cells?.changed?.disconnect(
          this.cellListListener);
    }
    if (this.validateIdsListener != null) {
      this.notebookPanel?.context?.saveState?.disconnect(
          this.validateIdsListener);
    }
    if (this.notebookDisposedListener != null) {
      this.notebookPanel?.disposed?.disconnect(this.notebookDisposedListener);
    }
    this.notebookPanel?.dispose();
    this.activeCell = null;
    this.activeCellWidgetListener = null;
    this.cellListener = null;
    this.cellListListener = null;
    this._cellMetadataChanged = null;
    this.cellWidgets = null;
    this.metadataChangedHandlers = null;
    this.notebookDisposedListener = null;
    this._notebookPanel = null;
    this.validateIdsListener = null;
    super.dispose();
  }

  private findCellInArray(model: ICellModel, cells: readonly Cell[]): Cell {
    return cells.find(
      (value: Cell, index: number, obj: readonly Cell[]) => {
        return value.model === model;
      });
  }

  private findDeadCell(cells: IterableIterator<Cell>): Cell {
    for (const cell of cells) {
      if (cell.model == null) {
        return cell;
      }
    }
    return undefined;
  }

  private getActiveCellListener(): (notebook: Notebook, cell: Cell) => void {
    return (notebook: Notebook, cell: Cell) => {
      if (this.activeCell != null) {
        const activeWidget = this.cellWidgets.get(this.activeCell);
        if (activeWidget != null) {
          activeWidget.setActive(false);
        }
      }
      if (cell != null) {
        const activeWidget = this.cellWidgets.get(cell);
        if (activeWidget != null) {
          activeWidget.setActive(true);
          this.scrollIntoViewNearest(activeWidget);
        }
      }
      this.activeCell = cell;
    }
  }

  private getActiveCellWidgetListener(): (cellWidget: CellWidget) => void {
    return (cellWidget: CellWidget) => {
      const i = this.notebookPanel.content.widgets.indexOf(cellWidget.cell);
      this.notebookPanel.content.activeCellIndex = i;
    }
  }

  private getNotebookDisposedListener(): (panel: NotebookPanel) => void {
    return (panel: NotebookPanel) => {
      this.dispose();
    }
  }

  private initCellWidgets(notebook: Notebook): void {
    for (const cell of notebook.widgets) {
      const cellWidget = this.addCellWidget(cell);
      cellWidget.setActive(notebook.activeCell === cell);
    }
  }

  private getMetadataChangedHandler(cellWidget: CellWidget):
      (metadata: IObservableJSON,
       args: IObservableMap.IChangedArgs<ReadonlyPartialJSONValue>) => void {
    return (metadata: IObservableJSON,
            args: IObservableMap.IChangedArgs<ReadonlyPartialJSONValue>) => {
      this.cellMetadataChanged.emit(cellWidget);
    }
  }

  private moveCellWidget(cell: Cell, index: number): void {
    const cellWidget = this.cellWidgets.get(cell);
    this.insertWidget(index, cellWidget);
  }

  /**
   * The notebook panel associated with this widget.
   */
  get notebookPanel(): NotebookPanel {
    return this._notebookPanel;
  }

  private removeCellWidget(cell: Cell): void {
    if (this.cellWidgets == null) {
      return;
    }
    const cellWidget = this.cellWidgets.get(cell);
    if (cellWidget == null) {
      return;
    }
    if (this.activeCellWidgetListener != null) {
      cellWidget.click?.disconnect(this.activeCellWidgetListener);
    }
    const handler = this.metadataChangedHandlers?.get(cellWidget);
    if (handler != null) {
      cell.model?.metadata?.changed?.disconnect(handler);
    }
    this.cellWidgets.delete(cell);
    cellWidget.dispose();
  }

  private validateIds(): void {
    const set = new Set<string>();
    const valid = /^[a-zA-Z0-9_\-]+$/;
    const iter = this.notebookPanel.model.cells.iter();
    for (let cellModel = iter.next(); cellModel != null; cellModel = iter.next()) {
      const data = CellModel.getNbgraderData(cellModel.metadata);

      if (data == null) continue;

      const id = data.grade_id;

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

  private validateSchemaVersion(): void {
    const iter = this.notebookPanel.model.cells.iter();
    for (let cellModel = iter.next(); cellModel != null;
         cellModel = iter.next()) {
      const data = CellModel.getNbgraderData(cellModel.metadata)
      let version = data == null ? null : data.schema_version;
      version = version === undefined ? 0 : version;
      if (version != null && version < NBGRADER_SCHEMA_VERSION) {
        this.warnSchemaVersion(version);
        return;
      }
    }
  }

  private warnInvalidId(badFormat: boolean, duplicateId: boolean, id: string):
      void {
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
      showErrorDialog(options);
      return;
    }
    else if (duplicateId) {
      options.title = 'Duplicate nbgrader cell ID';
      options.body = `The nbgrader ID "${id}" has been used for more than ` +
          `one cell. Please make sure all grade cells have unique ids.`;
      showErrorDialog(options);
      return;
    }
  }

  private warnSchemaVersion(schemaVersion: number): void {
    const version = schemaVersion.toString();
    const notebookPath = this.notebookPanel.sessionContext.path;
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
    showErrorDialog(options);
  }

  private scrollIntoViewNearest(widget: CellWidget): void {
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
  private cellListListener:
      (cellModels: IObservableUndoableList<ICellModel>,
       args: IObservableList.IChangedArgs<ICellModel>) => void;
  private cellModelListener:
      (notebookWidget: NotebookWidget, cellWidget: CellWidget) => void;
  private notebookHeaderWidget: NotebookHeaderWidget;
  private notebookWidget: NotebookWidget;

  constructor(panel: NotebookPanel) {
    super();
    this.addClass(CSS_NOTEBOOK_PANEL_WIDGET);
    this.initLayout(panel);
    this.setUpTotalPoints();
  }

  private calcTotalPoints(): number {
    let totalPoints = 0;
    const iter = this.notebookWidget.notebookPanel.model.cells.iter();
    for (let cellModel = iter.next(); cellModel != null;
         cellModel = iter.next()) {
      const data = CellModel.getNbgraderData(cellModel.metadata);
      const points = (data == null || data.points == null
                      || !CellModel.isGraded(data)) ? 0 : data.points;
      totalPoints += points;
    }
    return totalPoints;
  }

  dispose(): void {
    if (this.isDisposed) {
      return;
    }
    if (this.cellListListener != null) {
      this.notebookWidget?.notebookPanel?.model?.cells?.changed?.disconnect(
          this.cellListListener);
    }
    if (this.cellModelListener != null) {
      this.notebookWidget?.cellMetadataChanged?.disconnect(
          this.cellModelListener);
    }
    this.notebookHeaderWidget?.dispose();
    this.notebookWidget?.dispose();
    this.cellListListener = null;
    this.cellModelListener = null;
    this.notebookHeaderWidget = null;
    this.notebookWidget = null;
    super.dispose();
  }

  private initLayout(panel: NotebookPanel): void {
    this.notebookHeaderWidget = new NotebookHeaderWidget();
    this.notebookWidget = new NotebookWidget(panel);
    this.addWidget(this.notebookHeaderWidget);
    this.addWidget(this.notebookWidget);
  }

  private setUpTotalPoints(): void {
    this.notebookHeaderWidget.totalPoints = this.calcTotalPoints();
    this.cellListListener =
        (cellModels: IObservableUndoableList<ICellModel>,
         args: IObservableList.IChangedArgs<ICellModel>) => {
           if (args.type != 'move') {
             this.notebookHeaderWidget.totalPoints = this.calcTotalPoints();
           }
         };
    this.cellModelListener =
        (notebookWidget: NotebookWidget, cellWidget: CellWidget) => {
          this.notebookHeaderWidget.totalPoints = this.calcTotalPoints();
        };
    this.notebookWidget.notebookPanel.model.cells.changed.connect(
        this.cellListListener);
    this.notebookWidget.cellMetadataChanged.connect(this.cellModelListener);
  }
}
