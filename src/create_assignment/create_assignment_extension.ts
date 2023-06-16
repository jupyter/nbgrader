import { ILabShell } from '@jupyterlab/application';
import { Dialog, Styling } from '@jupyterlab/apputils';
import { Cell, ICellModel } from '@jupyterlab/cells';
import { IChangedArgs } from '@jupyterlab/coreutils';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import {
  INotebookModel,
  INotebookTracker,
  Notebook,
  NotebookPanel
} from '@jupyterlab/notebook';
import { CellList } from '@jupyterlab/notebook/lib/celllist';
import { IObservableList } from '@jupyterlab/observables';
import { IMapChange } from '@jupyter/ydoc';
import { ReadonlyPartialJSONValue } from '@lumino/coreutils';
import { Message } from '@lumino/messaging';
import { ISignal, Signal} from '@lumino/signaling';
import { Panel, Widget } from '@lumino/widgets';

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

  constructor(tracker: INotebookTracker, labShell: ILabShell | null) {
    super();
    this.addClass(CSS_CREATE_ASSIGNMENT_WIDGET);
    tracker.currentChanged.connect(this._onCurrentNotebookChange, this);
    if (labShell) {
      labShell.currentChanged.connect(this._onMainAreaActiveChange, this);
    }
    this._activeNotebook = null;
    this._notebookTracker = tracker;
    this._labShell = labShell;
  }

  /**
   * Dispose of the Panel.
   */
  dispose(): void {
    if (this.isDisposed) {
      return;
    }
    if (this._notebookPanelWidgets != null) {
      for (const widget of this._notebookPanelWidgets) {
        widget[1].dispose();
      }
    }
    this._notebookTracker.currentChanged.disconnect(
      this._onCurrentNotebookChange, this
    );
    if (this._labShell) {
      this._labShell.currentChanged.disconnect(this._onMainAreaActiveChange, this);
    }
    this._activeNotebook = null;
    this._notebookPanelWidgets = null;
    this._notebookTracker = null;
    super.dispose();
  }

  protected onBeforeShow(msg: Message): void {
    super.onBeforeShow(msg);
    if (this._activeNotebook != null){
      const notebookWidget = this._notebookPanelWidgets.get(this._activeNotebook);
      if (notebookWidget == null) {
        this._addNotebookWidget(this._notebookTracker, this._activeNotebook);
      }
      else {
        notebookWidget.show();
      }
    }
  }

  /**
   * Is the widget available (is there a notebook file visible in main area) ?
   */
  isAvailable(): boolean {
    if (this._activeNotebook === null) {
      return false;
    } else {
      return this._activeNotebook.isVisible;
    }
  }

  /*
   * Check if the widget must be visible :
   *  -> is there an active Notebook visible in main panel ?
   */
  protected onAfterShow(): void {
    if (!this._labShell) return;
    const widgets = this._labShell.widgets('main');
    if (this._activeNotebook == null){
      this._hideRightPanel();
    }
    else {
      for (let w of widgets) {
        if (w.title == this._activeNotebook.title) {
          if (!w.isVisible) this._hideRightPanel();
          else w.activate();
        }
      };
    }
  }

  /**
   * Add a notebook widget in the panel, which handle each cell of the notebookPanel.
   */
   private async _addNotebookWidget(
    tracker: INotebookTracker,
    panel: NotebookPanel
  ) {
    if (panel === null) return;

    await panel.revealed;
    const notebookPanelWidget = new NotebookPanelWidget(panel);
    this.addWidget(notebookPanelWidget);
    this._notebookPanelWidgets.set(panel, notebookPanelWidget);

    panel.disposed.connect(() => {
      notebookPanelWidget.dispose();
    });
    notebookPanelWidget.disposed.connect(() => {
      this._notebookPanelWidgets.delete(panel);
    });
    if (tracker.currentWidget != panel) {
      notebookPanelWidget.hide();
    }
    return panel.revealed;
  }

  /**
   * handle change of current notebook panel.
   */
  private async _onCurrentNotebookChange(
    tracker: INotebookTracker,
    panel: NotebookPanel
  ) {
    if (this._activeNotebook != null) {
      const widget = this._notebookPanelWidgets.get(this._activeNotebook);
      if (widget != null) {
        widget.hide();
      }
    }
    if (panel != null) {
      if (this.isVisible && this._notebookPanelWidgets.get(panel) == null) {
        await this._addNotebookWidget(tracker, panel);
      }
      const widget = this._notebookPanelWidgets.get(panel);
      if (widget != null) {
        widget.show();
      }
    }
    this._activeNotebook = panel;
  }

  /*
   * The listener on the main area tab change, to collapse
   * create_assignment widget if the current tab is not a Notebook.
   */
  private _onMainAreaActiveChange (
    shell: ILabShell,
    changed: ILabShell.IChangedArgs
  ) {
    if ( !(changed.newValue instanceof NotebookPanel) && this.isVisible) {
      this._hideRightPanel();
    }
  }

  /**
   * Hide the right panel.
   */
  private _hideRightPanel(): void {
    this._labShell.collapseRight();
  }

  private _activeNotebook: NotebookPanel;
  private _notebookPanelWidgets = new Map<NotebookPanel, NotebookPanelWidget>();
  private _notebookTracker: INotebookTracker;
  private _labShell: ILabShell;
}

/**
 * Shows a cell's assignment data.
 */
class CellWidget extends Panel {

  constructor(cellModel: ICellModel, notebookPanel?: NotebookPanel) {
    super();
    this._notebookPanel = notebookPanel;
    this._cellModel = cellModel;
    this._cellModel.metadataChanged.connect(
      this._onMetadataChange, this
    );
    this._initLayout();
    this._initInputListeners();
    this._initMetadata(cellModel);
    this.addClass(CSS_CELL_WIDGET);
    this.node.addEventListener('click', this._onClick.bind(this));
    this.cellModel.stateChanged.connect(this._onStateChange, this);

    // Try to update the prompt (works only if cell widget has been created).
    this._updatePrompt();
  }

  /**
   * The notebook cell associated with this widget.
   */
  get cellModel(): ICellModel {
    return this._cellModel;
  }

  private cleanNbgraderData(cellModel: ICellModel): void {
    CellModel.cleanNbgraderData(cellModel, cellModel.type);
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
    this.cellModel.metadataChanged.disconnect(
      this._onMetadataChange, this
    );
    this.node.removeEventListener('click', this._onClick);
    this.cellModel.stateChanged.disconnect(this._onStateChange, this);

    if (this._taskInput != null) {
      this._taskInput.onchange = null;
    }
    if (this._gradeIdInput != null) {
      this._gradeIdInput.onchange = null;
    }
    if (this._pointsInput != null) {
      this._pointsInput.onchange = null;
    }
    this._cellModel = null;
    this._click = null;
    this._lock = null;
    this._gradeId = null;
    this._points = null;
    this._taskInput = null;
    this._gradeIdInput = null;
    this._pointsInput = null;
    super.dispose();
  }

  /**
   * Sets this cell as active/focused.
   */
  setActive(active: boolean): void {
    if (active) {
      this.addClass(CSS_MOD_ACTIVE);

      // This _updatePrompt() call is a hack to create a prompt when a new cell is
      // added in cellList. Indeed the listener catches that a new cell model is added
      // to cellList, but not that the cell widget is created in the NotebookPanel.
      // The prompt is a copy of the one from the cell widget but there is no listener
      // on its creation. When a new cell is created, it is activated, so we use here
      // this activation to create the prompt.
      this._updatePrompt();
    } else {
      this.removeClass(CSS_MOD_ACTIVE);
    }
  }

  /**
   * Copy the prompt of the cell widget of the notebook.
   */
  private _updatePrompt() {
    this._headerElement.removeChild(this._promptNode);
    const cell: Cell = this._notebookPanel.content.widgets.find(widget => {
      return widget.model.id === this.cellModel.id
    });
    if (cell && cell.promptNode){
      this._promptNode = cell.promptNode.cloneNode(true) as HTMLElement;
    } else {
      this._promptNode = document.createElement('div');
    }
    this._headerElement.insertBefore(this._promptNode, this._headerElement.firstChild);
  }

  private _onStateChange(
    model: ICellModel,
    changedArgs: IChangedArgs<any, any, string>
  ) {
    if (changedArgs.name == 'executionCount') {
      this._updatePrompt();
    }
  }

  private _onMetadataChange (
    cellModel: ICellModel,
    changedArgs: IMapChange<ReadonlyPartialJSONValue>
  ) {
    const nbgraderData = CellModel.getNbgraderData(cellModel);
    const toolData = CellModel.newToolData(nbgraderData, this.cellModel.type);
    this._updateValues(toolData);
  }

  private _getOnInputChanged(): () => void {
    return () => {
      const toolData = new ToolData();
      toolData.type = this._taskInput.value as CellType;
      if (!this._gradeId.classList.contains(CSS_MOD_UNEDITABLE)) {
        toolData.id = this._gradeIdInput.value;
      }
      else {
        const nbgraderData = CellModel.getNbgraderData(this.cellModel);
        if (nbgraderData?.data.grade_id == null) {
          toolData.id = 'cell-' + this._randomString(16);
        }
        else {
          toolData.id = nbgraderData.data.grade_id;
        }
        this._gradeIdInput.value = toolData.id;
      }
      if (!this._points.classList.contains(CSS_MOD_UNEDITABLE)) {
        toolData.points = this._pointsInput.valueAsNumber;
      }
      const data = CellModel.newNbgraderData(toolData);
      CellModel.setNbgraderData(data, this.cellModel);
    }
  }

  private _getOnTaskInputChanged(): () => void {
    const onInputChanged = this._getOnInputChanged();
    return () => {
      onInputChanged();
      this._updateDisplayClass();
    }
  }

  private _onClick() {
    this._click.emit();
  }

  private _initInputListeners(): void {
    this._taskInput.onchange = this._getOnTaskInputChanged();
    this._gradeIdInput.onchange = this._getOnInputChanged();
    this._pointsInput.onchange = this._getOnInputChanged();
  }

  private _initLayout(): void {
    const bodyElement = document.createElement('div');
    const headerElement = this._newHeaderElement();
    const taskElement = this._newTaskElement();
    const idElement = this._newIdElement();
    const pointsElement = this._newPointsElement();
    const elements = [headerElement, taskElement, idElement, pointsElement];
    const fragment = document.createDocumentFragment();
    for (const element of elements) {
      fragment.appendChild(element);
    }
    bodyElement.appendChild(fragment);
    this.node.appendChild(bodyElement);
    this._headerElement = headerElement;
    this._lock = headerElement.getElementsByTagName('a')[0];
    this._gradeId = idElement;
    this._points = pointsElement;
    this._taskInput = taskElement.getElementsByTagName('select')[0];
    this._gradeIdInput = idElement.getElementsByTagName('input')[0];
    this._pointsInput = pointsElement.getElementsByTagName('input')[0];
  }

  private async _initMetadata(cellModel: ICellModel) {
    this.cleanNbgraderData(cellModel);
    const nbgraderData = CellModel.getNbgraderData(cellModel);
    const toolData = CellModel.newToolData(nbgraderData, this.cellModel.type);
    CellModel.clearCellType(cellModel);
    this._updateDisplayClass();
    this._updateValues(toolData);
  }

  private _newHeaderElement(): HTMLDivElement {
    const element = document.createElement('div');
    element.className = CSS_CELL_HEADER;
    this._promptNode = document.createElement('div');
    element.appendChild(this._promptNode);
    const lockElement = document.createElement('a');
    lockElement.className = CSS_LOCK_BUTTON;
    const listElement = document.createElement('li');
    listElement.className = 'fa fa-lock';
    listElement.title = 'Student changes will be overwritten';
    lockElement.appendChild(listElement);
    element.appendChild(lockElement);
    return element;
  }

  private _newIdElement(): HTMLDivElement {
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

  private _newPointsElement(): HTMLDivElement {
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

  private _newTaskElement(): HTMLDivElement {
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
    if (this.cellModel.type !== 'code') {
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

  private _randomString(length: number): string {
    var result = '';
    var chars = 'abcdef0123456789';
    var i;
    for (i = 0; i < length; i++) {
      result += chars[Math.floor(Math.random() * chars.length)];
    }
    return result;
  }

  private _setGradeId(value: string): void {
    this._gradeIdInput.value = value;
  }

  private _setElementEditable(element: HTMLElement, visible: boolean): void {
    if (visible) {
      element.classList.remove(CSS_MOD_UNEDITABLE);
    }
    else {
      element.classList.add(CSS_MOD_UNEDITABLE);
    }
  }

  private _setGradeIdEditable(visible: boolean): void {
    this._setElementEditable(this._gradeId, visible);
  }

  private _setPoints(value: number): void {
    this._pointsInput.value = value.toString();
  }

  private _setPointsEditable(visible: boolean): void {
    this._setElementEditable(this._points, visible);
  }

  private _setTask(value: string): void {
    this._taskInput.value = value;
  }

  private _updateDisplayClass(): void {
    const data = CellModel.getNbgraderData(this.cellModel);
    if (CellModel.isRelevantToNbgrader(data)) {
      this.addClass(CSS_MOD_HIGHLIGHT);
    }
    else {
      this.removeClass(CSS_MOD_HIGHLIGHT);
    }
  }

  private _updateValues(data: ToolData): void {
    this._setTask(data.type);
    if (data.id == null) {
      this._setGradeIdEditable(false);
      this._setGradeId('');
    }
    else {
      this._setGradeId(data.id);
      this._setGradeIdEditable(true);
    }
    if (data.points == null) {
      this._setPointsEditable(false);
      this._setPoints(0);
    }
    else {
      this._setPoints(data.points);
      this._setPointsEditable(true);
    }
    if (data.locked) {
      this._lock.classList.add(CSS_MOD_LOCKED);
    }
    else {
      this._lock.classList.remove(CSS_MOD_LOCKED);
    }
  }

  private _cellModel: ICellModel;
  private _notebookPanel: NotebookPanel | null;
  private _promptNode: HTMLElement;
  private _headerElement: HTMLDivElement;
  private _click = new Signal<this, void>(this);
  private _lock: HTMLAnchorElement;
  private _gradeId: HTMLDivElement;
  private _points: HTMLDivElement;
  private _taskInput: HTMLSelectElement;
  private _gradeIdInput: HTMLInputElement;
  private _pointsInput: HTMLInputElement;
}

/**
 * The header of a notebook's Create Assignment widget.
 *
 * Displays the total points in the notebook.
 */
class NotebookHeaderWidget extends Widget {

  constructor() {
    super();
    this.addClass(CSS_NOTEBOOK_HEADER_WIDGET);
    this._initLayout();
  }

  dispose(): void {
    if (this.isDisposed) {
      return;
    }
    this._pointsInput = null;
    super.dispose();
  }

  /**
   * The total points in the notebook.
   */
  set totalPoints(points: number) {
    if (this._pointsInput != null) {
      this._pointsInput.value = points.toString();
    }
  }

  private _initLayout(): void {
    const totalPoints = this._newTotalPointsElement();
    this.node.appendChild(totalPoints);
    this._pointsInput = totalPoints.getElementsByTagName('input')[0];
  }

  private _newTotalPointsElement(): HTMLDivElement {
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

  private _pointsInput: HTMLInputElement;
}

/**
 * Contains a list of {@link CellWidget}s for a notebook.
 */
class NotebookWidget extends Panel {

  constructor(panel: NotebookPanel) {
    super();
    this._activeCellModel = panel.content.activeCell.model;
    this._notebookPanel = panel;
    this.addClass(CSS_NOTEBOOK_WIDGET);
    this._initCellWidgets(panel.content);
    this._validateSchemaVersion();

    this._notebookPanel.content.activeCellChanged.connect(this._onActiveCellChange, this);
    this._notebookPanel.model.cells.changed.connect(this._onCellsListChange, this);
    this._notebookPanel.disposed.connect(this._onNotebookDisposed, this);
    this._notebookPanel.context.saveState.connect(this._onValidateIds, this);
  }

  dispose(): void {
    if (this.isDisposed) {
      return;
    }
    if (this._cellWidgets != null) {
      for (const widgets of this._cellWidgets) {
        this._removeCellWidget(widgets[1]);
      }
    }
    this.notebookPanel?.content?.activeCellChanged?.disconnect(
      this._onActiveCellChange, this
    );
    this.notebookPanel?.model?.cells?.changed?.disconnect(
      this._onCellsListChange, this
    );
    this.notebookPanel?.context?.saveState?.disconnect(
      this._onValidateIds, this
    );
    this.notebookPanel?.disposed?.disconnect(this._onNotebookDisposed, this);

    this.notebookPanel?.dispose();
    this._activeCellModel = null;
    this._cellMetadataChanged = null;
    this._cellWidgets = null;
    this._notebookPanel = null;
    super.dispose();
  }

  /**
   * A signal which is evoked when one of the cell's metadata changes.
   */
  get cellMetadataChanged(): Signal<this, CellWidget> {
    return this._cellMetadataChanged;
  }

  /**
   * The notebook panel associated with this widget.
   */
  get notebookPanel(): NotebookPanel {
    return this._notebookPanel;
  }

  private _onCellsListChange (
    sender: CellList,
    args: IObservableList.IChangedArgs<ICellModel>
  ) {
    switch (args.type) {
      case 'add': {
        this._addCellWidget(args.newValues[0], args.newIndex);
      break;
      }
      case 'move': {
        const cellModel = this._notebookPanel.model.cells.get(args.newIndex)
        this._moveCellWidget(cellModel, args.newIndex);
        break;
      }
      case 'remove': {
        this._cleanCellWidgets();
        break;
      }
      case 'set': {
        // Existing notebook cell changed. Update the corresponding widget.
        // const oldCell = this.findDeadCell(this.cellWidgets.keys());
        const oldCell = args.oldValues[0]
        if (oldCell != null) {
          const newCell = args.newValues[0];
          this._cellWidgets.get(oldCell).dispose();
          this._cellWidgets.delete(oldCell);
          const cellWidget = this._addCellWidget(newCell, args.newIndex);
          cellWidget.setActive(this._activeCellModel === newCell);
          if (this._activeCellModel === newCell) {
            this._scrollIntoViewNearest(cellWidget);
          }
        }
      }
    }
  }

  private _addCellWidget(cellModel: ICellModel, index = undefined as number): CellWidget {
    const cellWidget = new CellWidget(cellModel, this._notebookPanel);
    this._cellWidgets.set(cellModel, cellWidget);
    if (index == null) {
      this.addWidget(cellWidget);
    }
    else {
      this.insertWidget(index, cellWidget);
    }
    cellWidget.click.connect(this._activeCellWidgetListener, this);
    const metadataChangedHandler = this._getMetadataChangedHandler(cellWidget);
    cellModel.metadataChanged.connect(metadataChangedHandler);
    return cellWidget;
  }

  private _onValidateIds(
    context: DocumentRegistry.IContext<INotebookModel>,
    args: DocumentRegistry.SaveState
  ) {
    if (args != 'started') {
      return;
    }
    this._validateIds();
  }

  /**
   * Called when the selected cell on notebook panel changes.
   */
  private _onActiveCellChange(
    notebook: Notebook,
    cell: Cell
  ): void {

    if (cell !== null ){
      cell.ready.then(() => {
        this._cellWidgets.get(this._activeCellModel)?.setActive(false);
        this._activeCellModel = cell.model;
        const activeWidget = this._cellWidgets.get(cell.model);
        activeWidget?.setActive(true);
        if (activeWidget) {
          this._scrollIntoViewNearest(activeWidget);
        }
      })
    }
    else {
      this._cellWidgets.get(this._activeCellModel)?.setActive(false);
      this._activeCellModel = null;
    }
  }

  /**
   * Called when the selected widget on this panel changes.
   */
  private _activeCellWidgetListener(cellWidget: CellWidget) {
    const cell: Cell = this.notebookPanel.content.widgets.find(widget => {
      return widget.model.id === cellWidget.cellModel.id
    });
    this.notebookPanel.content.activeCellIndex = this.notebookPanel.content.widgets.indexOf(cell);
  }

  /**
   * When the notebook panel is disposed.
   */
  private _onNotebookDisposed(panel: NotebookPanel) {
    this.dispose();
  }

  private _initCellWidgets(notebook: Notebook): void {
    for (const cell of notebook.widgets) {
      const cellWidget = this._addCellWidget(cell.model);
      cellWidget.setActive(notebook.activeCell === cell);
    }
  }

  private _getMetadataChangedHandler(cellWidget: CellWidget): (
    cellModel: ICellModel,
    changedArgs: IMapChange<ReadonlyPartialJSONValue>
  ) => void {
    return (
      cellModel: ICellModel,
      changedArgs: IMapChange<ReadonlyPartialJSONValue>
    ) => {
      this.cellMetadataChanged.emit(cellWidget);
    }
  }

  private _moveCellWidget(cell: ICellModel, index: number): void {
    const cellWidget = this._cellWidgets.get(cell);
    this.insertWidget(index, cellWidget);
  }

  private _removeCellWidget(widget: CellWidget): void {
    widget.click?.disconnect(this._activeCellWidgetListener, this);
    this._cellWidgets.delete(widget.cellModel);
    widget.dispose();
  }

  private _cleanCellWidgets(): void {
    if (this._cellWidgets == null) {
      return;
    }

    const widgetsToRemove = Array
      .from(this._cellWidgets.values())
      .filter(widget => widget.cellModel.isDisposed);

    widgetsToRemove.forEach(widget => {
      this._removeCellWidget(widget);
    });
  }

  private _validateIds(): void {
    const set = new Set<string>();
    const valid = /^[a-zA-Z0-9_\-]+$/;
    for (let cellModel of this.notebookPanel.model.cells) {
      const nbgraderData = CellModel.getNbgraderData(cellModel);

      if (nbgraderData == null) continue;

      const id = nbgraderData.data.grade_id;

      if (!valid.test(id)) {
        this._warnInvalidId(true, false, id);
        return;
      }
      else if (set.has(id)) {
        this._warnInvalidId(false, true, id);
        return;
      }
      else {
        set.add(id);
      }
    }
  }

  private _validateSchemaVersion(): void {
    for (let cellModel of this.notebookPanel.model.cells) {
      const nbgraderData = CellModel.getNbgraderData(cellModel)
      let version = (nbgraderData === null) ? null : nbgraderData.data.schema_version;
      version = version === undefined ? 0 : version;
      if (version != null && version < NBGRADER_SCHEMA_VERSION) {
        this._warnSchemaVersion(version);
        return;
      }
    }
  }

  private _warnInvalidId(badFormat: boolean, duplicateId: boolean, id: string):
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

  private _warnSchemaVersion(schemaVersion: number): void {
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

  private _scrollIntoViewNearest(widget: CellWidget): void {
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

  private _activeCellModel: ICellModel | null = null;
  private _cellMetadataChanged = new Signal<this, CellWidget>(this);
  private _cellWidgets = new Map<ICellModel, CellWidget>();
  private _notebookPanel: NotebookPanel;
}

/**
 * Contains a notebook's "Create Assignment" UI.
 */
class NotebookPanelWidget extends Panel {

  constructor(panel: NotebookPanel) {
    super();
    this.addClass(CSS_NOTEBOOK_PANEL_WIDGET);
    this._initLayout(panel);
    this._notebookHeaderWidget.totalPoints = this._calcTotalPoints();
    panel.model.cells.changed.connect(
      this._onCellListChange, this
    );
    this._notebookWidget.cellMetadataChanged.connect(
      this._onCellMetadataChange, this
    );
  }

  dispose(): void {
    if (this.isDisposed) {
      return;
    }
    this._notebookWidget.notebookPanel.model.cells.changed.disconnect(
      this._onCellListChange, this
    );
    this._notebookWidget.cellMetadataChanged.disconnect(
      this._onCellMetadataChange, this
    );
    this._notebookHeaderWidget?.dispose();
    this._notebookWidget?.dispose();
    this._notebookHeaderWidget = null;
    this._notebookWidget = null;
    super.dispose();
  }


  private _calcTotalPoints(): number {
    let totalPoints = 0;
    for (let cellModel of this._notebookWidget.notebookPanel.model.cells) {
      const nbgraderData = CellModel.getNbgraderData(cellModel);
      const points = (nbgraderData === null || nbgraderData.data.points === null
                      || !nbgraderData?.isGradable()) ? 0 : nbgraderData.data?.points;
      totalPoints += points;
    }
    return totalPoints;
  }

  private _initLayout(panel: NotebookPanel): void {
    this._notebookHeaderWidget = new NotebookHeaderWidget();
    this._notebookWidget = new NotebookWidget(panel);
    this.addWidget(this._notebookHeaderWidget);
    this.addWidget(this._notebookWidget);
  }

  /**
   * handle event on the cell list of the NotebookPanel.
   */
  private _onCellListChange (
    cellModels: CellList,
    args: IObservableList.IChangedArgs<ICellModel>
  ) {
    if (args.type != 'move') {
      this._notebookHeaderWidget.totalPoints = this._calcTotalPoints();
    }
  }

  /**
   * handle changes on the Cell widget metadata;
   */
  private _onCellMetadataChange(notebookWidget: NotebookWidget, cellWidget: CellWidget) {
    this._notebookHeaderWidget.totalPoints = this._calcTotalPoints();
  }

  private _notebookHeaderWidget: NotebookHeaderWidget;
  private _notebookWidget: NotebookWidget;
}
