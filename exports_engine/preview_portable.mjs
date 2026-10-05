import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
for(const mode of ['class','student']){
 const w=await SpreadsheetFile.importXlsx(await FileBlob.load('outputs/export-qa/'+mode+'-portable.xlsx'));
 const p=await w.render({sheetName:'Les 01 04-10',range:mode==='class'?'A1:H24':'A1:E24',scale:1,format:'png'});
 await fs.writeFile('outputs/export-qa/'+mode+'-portable.png',new Uint8Array(await p.arrayBuffer()));
 console.log(mode,'rendered');
}

