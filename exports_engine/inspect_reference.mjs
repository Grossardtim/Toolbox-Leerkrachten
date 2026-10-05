import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load('Evaluatie 6HV.xlsx'));
await fs.mkdir('outputs/export-qa', {recursive:true});
const preview = await workbook.render({sheetName:'Evaluatie Les', range:'A1:I16', scale:1, format:'png'});
await fs.writeFile('outputs/export-qa/reference.png', new Uint8Array(await preview.arrayBuffer()));
console.log('Reference rendered');
