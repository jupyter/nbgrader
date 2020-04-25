import * as nbformat from '@jupyterlab/nbformat';

import {
  IObservableJSON
} from '@jupyterlab/observables';

import {
  JSONObject,
  ReadonlyJSONObject
} from '@lumino/coreutils';

const NBGRADER_KEY = 'nbgrader';

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
    const nbgraderData = new NbgraderData();
    // TODO
    switch (data.type) {
      case '':
        return null;
      case 'manual':
        break;
      case 'task':
        break;
      case 'solution':
        break;
      case 'tests':
        break;
      case 'readonly':
        break;
    }
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

    if (Private.isInvalid(data, cellType)) {
      toolData.type = '';
      return toolData;
    }
    toolData.type = Private.getType(data, cellType);
    if (toolData.type === '') {
      return toolData;
    }

    if (Private.isGrade(data) || Private.isSolution(data) ||
        Private.isLocked(data)) {
      toolData.id = Private.getGradeId(data);
    }

    if (Private.isGraded(data)) {
      toolData.points = Private.getPoints(data);
    }

    toolData.locked = Private.isLocked(data);

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
    }
    cellMetadata.set(NBGRADER_KEY, data.toJson());
  }
}

namespace Private {
  export function getGradeId(nbgraderData: NbgraderData): string {
    if (nbgraderData == null || nbgraderData.grade_id == null) {
      return 'cell-' + Private._randomString(16);
    }
    return nbgraderData.grade_id;
  }

  export function getPoints(nbgraderData: NbgraderData): number {
    if (nbgraderData == null) {
      return 0;
    }
    return Private._to_float(nbgraderData.points);
  }

  export function getSchemeaVersion(nbgraderData: NbgraderData): number {
    if (nbgraderData === null) {
      return 0;
    }
    return nbgraderData.schema_version;
  }

  export function getType(nbgraderData: NbgraderData,
                          cellType: nbformat.CellType): CellType {
    if (Private.isTask(nbgraderData)) {
      return 'task';
    } else if (Private.isSolution(nbgraderData) && isGrade(nbgraderData)) {
      return 'manual';
    } else if (Private.isSolution(nbgraderData) && cellType === 'code') {
      return 'solution';
    } else if (Private.isGrade(nbgraderData) && cellType === 'code') {
      return 'tests';
    } else if (Private.isLocked(nbgraderData)) {
      return 'readonly';
    } else {
      return '';
    }
  }

  export function isGrade(nbgraderData: NbgraderData): boolean {
    return nbgraderData != null && nbgraderData.grade === true;
  }

  export function isGraded(nbgraderData: NbgraderData): boolean {
    return Private.isGrade(nbgraderData) || Private.isTask(nbgraderData);
  }

  export function isInvalid(nbgraderData: NbgraderData,
                            cellType: nbformat.CellType): boolean {
    return !Private.isTask(nbgraderData) && cellType !== 'code'
        && (Private.isSolution(nbgraderData) != Private.isGrade(nbgraderData));
  }

  export function isLocked(nbgraderData: NbgraderData): boolean {
    return !Private.isSolution(nbgraderData) && (Private.isGraded(nbgraderData)
        || (nbgraderData != null && nbgraderData.locked === true));
  }

  export function isSolution(nbgraderData: NbgraderData): boolean {
    return nbgraderData != null && nbgraderData.solution === true;
  }

  export function isTask(nbgraderData: NbgraderData): boolean {
    return nbgraderData != null && nbgraderData.task === true;
  }

  export function _randomString(length: number): string {
    var result = '';
    var chars = 'abcdef0123456789';
    var i;
    for (i = 0; i < length; i++) {
      result += chars[Math.floor(Math.random() * chars.length)];
    }
    return result;
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
