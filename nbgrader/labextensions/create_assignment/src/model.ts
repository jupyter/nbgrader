import * as nbformat from '@jupyterlab/nbformat';

import {
  IObservableJSON
} from '@jupyterlab/observables';

import {
  JSONObject,
  ReadonlyJSONObject
} from '@lumino/coreutils';

const NBGRADER_KEY = 'nbgrader';
const NBGRADER_SCHEMA_VERSION = 3;

/**
 * A namespace for conversions between {@link NbgraderData} and
 * {@link ToolData} and for reading and writing to notebook cells' metadata.
 */
export namespace CellModel {
  /**
   * Read the nbgrader data from a cell's metadata.
   *
   * @returns The nbgrader data, or null if it doesn't exist.
   */
  export function getNbgraderData(cellMetadata: IObservableJSON): NbgraderData {
    if (cellMetadata == null) {
      return null;
    }
    const nbgraderValue = cellMetadata.get('nbgrader');
    if (nbgraderValue == null) {
      return null;
    }
    return nbgraderValue.valueOf() as NbgraderData;
  }

  /**
   * Converts {@link ToolData} to {@link NbgraderData}.
   *
   * @returns The converted data, or null if the nbgrader cell type is not set.
   */
  export function newNbgraderData(data: ToolData): NbgraderData {
    if (data.type === '') {
      return null;
    }
    const nbgraderData = new NbgraderData();
    nbgraderData.grade = PrivateToolData.getGrade(data);
    nbgraderData.grade_id = PrivateToolData.getGradeId(data);
    nbgraderData.locked = PrivateToolData.getLocked(data);
    nbgraderData.points = PrivateToolData.getPoints(data);
    nbgraderData.schema_version = PrivateToolData.getSchemeaVersion();
    nbgraderData.solution = PrivateToolData.getSolution(data);
    nbgraderData.task = PrivateToolData.getTask(data);
    return nbgraderData;
  }

  /**
   * Converts {@link NbgraderData} to {@link ToolData}.
   *
   * @param data The data to convert. Can be null.
   * @param cellType The notebook cell widget type.
   */
  export function newToolData(data: NbgraderData, cellType: nbformat.CellType):
      ToolData {
    const toolData = new ToolData;

    if (PrivateNbgraderData.isInvalid(data, cellType)) {
      toolData.type = '';
      return toolData;
    }
    toolData.type = PrivateNbgraderData.getType(data, cellType);
    if (toolData.type === '') {
      return toolData;
    }

    if (PrivateNbgraderData.isGrade(data)
        || PrivateNbgraderData.isSolution(data)
        || PrivateNbgraderData.isLocked(data)) {
      toolData.id = PrivateNbgraderData.getGradeId(data);
    }

    if (PrivateNbgraderData.isGraded(data)) {
      toolData.points = PrivateNbgraderData.getPoints(data);
    }

    toolData.locked = PrivateNbgraderData.isLocked(data);

    return toolData;
  }

  /**
   * Writes the nbgrader data to a cell's metadata.
   *
   * @param data The nbgrader data. If null, the nbgrader entry, if it exists,
   * will be removed from the metadata.
   */
  export function setNbgraderData(data: NbgraderData, cellMetadata:
                                  IObservableJSON): void {
    if (data == null) {
      if (cellMetadata.has(NBGRADER_KEY)) {
        cellMetadata.delete(NBGRADER_KEY);
      }
      return;
    }
    const currentDataJson = cellMetadata.get(NBGRADER_KEY);
    const currentData = currentDataJson == null ? null :
        currentDataJson.valueOf() as NbgraderData;
    if (currentData != data) {
      cellMetadata.set(NBGRADER_KEY, data.toJson());
    }
  }
}

namespace PrivateNbgraderData {
  export function getGradeId(nbgraderData: NbgraderData): string {
    if (nbgraderData == null || nbgraderData.grade_id == null) {
      return '';
    }
    return nbgraderData.grade_id;
  }

  export function getPoints(nbgraderData: NbgraderData): number {
    if (nbgraderData == null) {
      return 0;
    }
    return PrivateNbgraderData._to_float(nbgraderData.points);
  }

  export function getSchemeaVersion(nbgraderData: NbgraderData): number {
    if (nbgraderData === null) {
      return 0;
    }
    return nbgraderData.schema_version;
  }

  export function getType(nbgraderData: NbgraderData,
                          cellType: nbformat.CellType): CellType {
    if (PrivateNbgraderData.isTask(nbgraderData)) {
      return 'task';
    } else if (PrivateNbgraderData.isSolution(nbgraderData)
               && isGrade(nbgraderData)) {
      return 'manual';
    } else if (PrivateNbgraderData.isSolution(nbgraderData)
               && cellType === 'code') {
      return 'solution';
    } else if (PrivateNbgraderData.isGrade(nbgraderData)
               && cellType === 'code') {
      return 'tests';
    } else if (PrivateNbgraderData.isLocked(nbgraderData)) {
      return 'readonly';
    } else {
      return '';
    }
  }

  export function isGrade(nbgraderData: NbgraderData): boolean {
    return nbgraderData != null && nbgraderData.grade === true;
  }

  export function isGraded(nbgraderData: NbgraderData): boolean {
    return PrivateNbgraderData.isGrade(nbgraderData)
        || PrivateNbgraderData.isTask(nbgraderData);
  }

  export function isInvalid(nbgraderData: NbgraderData,
                            cellType: nbformat.CellType): boolean {
    return !PrivateNbgraderData.isTask(nbgraderData) && cellType !== 'code'
        && (PrivateNbgraderData.isSolution(nbgraderData)
            != PrivateNbgraderData.isGrade(nbgraderData));
  }

  export function isLocked(nbgraderData: NbgraderData): boolean {
    return !PrivateNbgraderData.isSolution(nbgraderData)
        && (PrivateNbgraderData.isGraded(nbgraderData)
            || (nbgraderData != null && nbgraderData.locked === true));
  }

  export function isSolution(nbgraderData: NbgraderData): boolean {
    return nbgraderData != null && nbgraderData.solution === true;
  }

  export function isTask(nbgraderData: NbgraderData): boolean {
    return nbgraderData != null && nbgraderData.task === true;
  }

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
    return data.id == null ? '' : data.id;
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

/**
 * Dummy class for representing the nbgrader cell metadata.
 */
export class NbgraderData {
  grade: boolean;
  grade_id: string;
  locked: boolean;
  points: number;
  schema_version: number;
  solution: boolean;
  task: boolean;

  toJson(): ReadonlyJSONObject {
    const json = {} as JSONObject;
    if (this.grade != null) {
      json['grade'] = this.grade;
    }
    if (this.grade_id != null) {
      json['grade_id'] = this.grade_id;
    }
    if (this.locked != null) {
      json['locked'] = this.locked;
    }
    if (this.points != null) {
      json['points'] = this.points;
    }
    if (this.schema_version != null) {
      json['schema_version'] = this.schema_version;
    }
    if (this.solution != null) {
      json['solution'] = this.solution;
    }
    if (this.task != null) {
      json['task'] = this.task;
    }
    return json;
  }
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
