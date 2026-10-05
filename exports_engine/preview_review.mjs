import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const w=await SpreadsheetFile.importXlsx(await FileBlob.load('outputs/export-qa/class-review.xlsx'));
for(const [sheet,range,key] of [['Klasoverzicht evaluaties','A11:H24','summary'],['Les 01 04-10','A10:H30','lesson'],['Feedback','A11:G18','feedback']]){
 const p=await w.render({sheetName:sheet,range,scale:1,format:'png'});
 await fs.writeFile('outputs/export-qa/review-'+key+'.png',new Uint8Array(await p.arrayBuffer()));
}
console.log('Drie werkbladen gerenderd');
