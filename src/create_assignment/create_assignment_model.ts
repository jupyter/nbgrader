import { ICellModel } from '@jupyterlab/cells';
import * as nbformat from '@jupyterlab/nbformat';

import {
  JSONObject,
  ReadonlyJSONObject
} from '@lumino/coreutils';

const NBGRADER_KEY = 'nbgrader';
export const NBGRADER_SCHEMA_VERSION = 4;

/**
 * A namespace for conversions between {@link NbgraderMetadata} and
 * {@link ToolData} and for reading and writing to notebook cells' metadata.
 */
export namespace CellModel {
  /**
   * Cleans invalid nbgrader data if necessary.
   *
   * @returns Whether cleaning occurred.
   */
  export function cleanNbgraderData(
    cellModel: ICellModel,
    cellType: nbformat.CellType
  ): boolean {
    const data = CellModel.getNbgraderData(cellModel);
    if (data === null || !data?.isInvalid(cellType)) {
      return false;
    }

    data.data.schema_version= NBGRADER_SCHEMA_VERSION;
    data.data.solution= false;
    data.data.grade= false;
    data.data.locked= false;
    data.data.task= false;

    setNbgraderData(data, cellModel);

    return true;
  }

  /**
   * Removes the "cell_type" property from the nbgrader data.
   */
  export function clearCellType(cellModel: ICellModel): void {
    const data = cellModel.getMetadata(NBGRADER_KEY) as JSONObject;
    if (data == null) {
      return;
    }
    if ('cell_type' in data) {
      data['cell_type'] = undefined;
    }
    cellModel.setMetadata(NBGRADER_KEY, data);
  }

  /**
   * Read the nbgrader data from a cell's metadata.
   *
   * @returns The nbgrader data, or null if it doesn't exist.
   */
  export function getNbgraderData(cellModel: ICellModel): NbgraderMetadata {
    if (cellModel === null) {
      return null;
    }
    const nbgraderValue = cellModel.getMetadata(NBGRADER_KEY);
    if (nbgraderValue === undefined) {
      return null;
    }
    return new NbgraderMetadata(nbgraderValue.valueOf() as NbgraderData);
  }

  /**
   * @returns True if the cell is gradable.
   */
  export function isGraded(data: NbgraderMetadata): boolean {
    return data?.isGradable();
  }

  /**
   * @returns True if the cell relevant to nbgrader. A cell is relevant if it is
   * gradable or contains autograder tests.
   */
  export function isRelevantToNbgrader(data: NbgraderMetadata): boolean {
    return data?.isGradable() || data?.isSolution();
  }

  /**
   * Converts {@link ToolData} to {@link NbgraderMetadata}.
   *
   * @returns The converted data, or null if the nbgrader cell type is not set.
   */
  export function newNbgraderData(data: ToolData): NbgraderMetadata {
    if (data.type === '') {
      return null;
    }

    const nbgraderData = {
      grade: PrivateToolData.getGrade(data),
      grade_id: PrivateToolData.getGradeId(data),
      locked: PrivateToolData.getLocked(data),
      points: PrivateToolData.getPoints(data),
      schema_version: PrivateToolData.getSchemeaVersion(),
      solution: PrivateToolData.getSolution(data),
      task: PrivateToolData.getTask(data)
    }
    return new NbgraderMetadata(nbgraderData);
  }

  /**
   * Converts {@link NbgraderMetadata} to {@link ToolData}.
   *
   * @param data The data to convert. Can be null.
   * @param cellType The notebook cell widget type.
   */
  export function newToolData(data: NbgraderMetadata, cellType: nbformat.CellType):
      ToolData {
    const toolData = new ToolData;

    if (data?.isInvalid(cellType)) {
      toolData.type = '';
      return toolData;
    }
    toolData.type = data?.getType(cellType) || '';
    if (toolData.type === '') {
      return toolData;
    }

    if (data?.isGrade() || data?.isSolution() || data?.isLocked()) {
      toolData.id = data?.getGradeId() || '';
    }

    if (data?.isGradable()) {
      toolData.points = data?.getPoints() || 0;
    }

    toolData.locked = data?.isLocked() || false;

    return toolData;
  }

  /**
   * Writes the nbgrader data to a cell's metadata.
   *
   * @param data The nbgrader data. If null, the nbgrader entry, if it exists,
   * will be removed from the metadata.
   */
  export function setNbgraderData(
    data: NbgraderMetadata,
    cellModel: ICellModel): void
  {
    if (data === null) {
      if (cellModel.getMetadata(NBGRADER_KEY)) {
        cellModel.deleteMetadata(NBGRADER_KEY);
      }
      return;
    }
    cellModel.setMetadata(NBGRADER_KEY, data.toJson());
  }
}

namespace Private {

  export function _to_float(val: any): number {
    if (val == null || val === '') {
      return 0;
    }
    const valType = typeof(val);
    if (valType === 'string') {
      return parseFloat(val);
    }
    else if (valType === 'number') {
      return val;
    }
    return 0;
  }
}

namespace PrivateToolData {
  export function getGrade(data: ToolData): boolean {
    return data.type === 'manual' || data.type === 'tests';
  }

  export function getGradeId(data: ToolData): string {
    return data.id === null ? '' : data.id;
  }

  export function getLocked(data: ToolData): boolean {
    if (PrivateToolData.getSolution(data)) {
      return false;
    }
    if (PrivateToolData.getGrade(data)) {
      return true;
    }
    return data.type === 'task' || data.type === 'tests'
        || data.type === 'readonly';
  }

  export function getPoints(data: ToolData): number {
    if (!PrivateToolData.getGrade(data) && !PrivateToolData.getTask(data)) {
      return undefined;
    }
    return data.points >= 0 ? data.points : 0;
  }

  export function getSchemeaVersion(): number {
    return NBGRADER_SCHEMA_VERSION;
  }

  export function getSolution(data: ToolData): boolean {
    return data.type === 'manual' || data.type === 'solution';
  }

  export function getTask(data: ToolData): boolean {
    return data.type === 'task';
  }
}

export interface INbgraderMetadata {

  isGrade(): boolean;
  isGradable(): boolean;
  isInvalid(cellType: nbformat.CellType): boolean;
  isLocked(): boolean;
  isTask(): boolean;
  isSolution(): boolean;
  toJson(): ReadonlyJSONObject;

  data: NbgraderData;
}
/**
 * Dummy class for representing the nbgrader cell metadata.
 */
export class NbgraderMetadata implements INbgraderMetadata{

  constructor(data: NbgraderData) {

    this._data = data;
  }

  get data(): NbgraderData {
    return this._data;
  }
  set data(value: NbgraderData) {
    this._data = value;
  }

  getGradeId(): string {
    return this.data.grade_id || '';
  }

  getPoints(): number {
    return Private._to_float(this.data.points || 0);
  }

  getSchemaVersion(): number {
    return this.data?.schema_version || NBGRADER_SCHEMA_VERSION;
  }

  getType(cellType: nbformat.CellType): CellType {
    if (this.isTask()) {
      return 'task';
    } else if (this.isSolution() && this.isGrade()) {
      return 'manual';
    } else if (this.isSolution() && cellType === 'code') {
      return 'solution';
    } else if (this.isGrade() && cellType === 'code') {
      return 'tests';
    } else if (this.isLocked()) {
      return 'readonly';
    } else {
      return '';
    }
  }

  isGrade(): boolean {
    return this._data.grade || false;
  }

  isGradable(): boolean {
    return this.isGrade() || this.isTask();
  }

  isInvalid(cellType: nbformat.CellType): boolean {
    return !this.isTask()
      && cellType !== 'code'
      && (this.isSolution() !== this.isGrade());
  }

  isLocked(): boolean {
    return !this.isSolution() && (this.isGradable() || this._data.locked);
  }

  isTask(): boolean {
    return this._data.task || false;
  }

  isSolution(): boolean {
    return this._data.solution || false;
  }

  toJson(): ReadonlyJSONObject {
    const json = {} as JSONObject;
    if (this.data.grade !== undefined) {
      json['grade'] = this.data.grade;
    }
    if (this.data.grade_id !== undefined) {
      json['grade_id'] = this.data.grade_id;
    }
    if (this.data.locked !== undefined) {
      json['locked'] = this.data.locked;
    }
    if (this.data.points !== undefined) {
      json['points'] = this.data.points;
    }
    if (this.data.schema_version !== undefined) {
      json['schema_version'] = this.data.schema_version;
    }
    if (this.data.solution !== undefined) {
      json['solution'] = this.data.solution;
    }
    if (this.data.task !== undefined) {
      json['task'] = this.data.task;
    }
    return json;
  }

  private _data: NbgraderData = {};
}

type NbgraderData = {
  grade?: boolean;
  grade_id?: string;
  locked?: boolean;
  points?: number;
  schema_version?: number;
  solution?: boolean;
  task?: boolean;
}
/**
 * Dummy class for representing the UI input/output values.
 */
export class ToolData {
  type: CellType;
  id: string;
  points: number;
  locked: boolean;
}

export type CellType = '' | 'manual' | 'task' | 'solution' | 'tests' |
    'readonly';
