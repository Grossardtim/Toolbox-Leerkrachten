import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

const [inputPath, outputPath, previewPath] = process.argv.slice(2);
if (!inputPath || !outputPath) throw new Error('Input and output paths required.');
const data = JSON.parse(await fs.readFile(inputPath, 'utf8'));
const workbook = Workbook.create();
const accent = '#B80045', soft = '#F5E8EE', ink = '#27252B', muted = '#6E6570';
const individual = data.mode === 'student';
const logo = await fs.readFile(path.join(path.dirname(fileURLToPath(import.meta.url)), '../static/school-logo.png'));
const text = value => {
  const str = String(value ?? '').replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '');
  return /^[=+@-]/.test(str) ? "'" + str : str;
};
function column(index) {
  let result = '';
  for (let n = index; n > 0; n = Math.floor((n - 1) / 26)) result = String.fromCharCode(65 + (n - 1) % 26) + result;
  return result;
}
function set(sheet, address, value) {sheet.getRange(address).values = [[typeof value === 'string' ? text(value) : value]];}
function formula(sheet, address, value) {sheet.getRange(address).formulas = [[value]];}
function merged(sheet, address, value) {sheet.mergeCells(address); set(sheet, address.split(':')[0], value);}
function labelRow(sheet, row, value, end=4) {merged(sheet, `A${row}:${column(end)}${row}`, value);}
function header(sheet, address) {
  sheet.getRange(address).format = {fill:accent, font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},
    horizontalAlignment:'center', verticalAlignment:'center',wrapText:true};
}
function base(sheet, title, subtitle, lastColumn) {
  const last = column(lastColumn);
  sheet.showGridLines = false;
  sheet.tabColor = accent;
  sheet.getRange(`A1:${last}12`).format.font = {name:'Arial',size:10,color:ink};
  sheet.getRange(`A1:D200`).format.columnWidth = 13;
  sheet.getRange(`E1:${last}200`).format.columnWidth = 20;
  sheet.getRange(`A1:${last}3`).format.rowHeight = 22;
  sheet.images.add({dataUrl:`data:image/png;base64,${logo.toString('base64')}`,
    anchor:{from:{row:0,col:0},extent:{widthPx:200,heightPx:71}}});
  merged(sheet,`D1:${last}3`,data.school);
  sheet.getRange(`D1:${last}3`).format={font:{name:'Arial',size:12,bold:true,color:accent},wrapText:true,verticalAlignment:'center'};
  merged(sheet, `A5:${last}5`, title);
  sheet.getRange(`A5:${last}5`).format = {font:{name:'Arial',size:16,bold:true,color:ink},rowHeight:36};
  merged(sheet, `A6:${last}6`, subtitle);
  sheet.getRange(`A6:${last}6`).format = {font:{name:'Arial',size:10,color:muted},wrapText:true,rowHeight:32};
  merged(sheet, `A7:${last}7`, `${data.className} · ${data.direction} · Schooljaar ${data.schoolYear}`);
  sheet.getRange(`A7:${last}7`).format = {wrapText:true,rowHeight:30};
  merged(sheet, `A9:${last}9`, 'Scores: 0 / 20 / 40 / 60 / 80. Afwezig en leeg tellen niet mee; 0 wel. Geen omzetting naar 100.');
  sheet.getRange(`A9:${last}9`).format = {font:{name:'Arial',size:9,color:muted},wrapText:true,rowHeight:32};
}
function body(sheet, from, to, last) {
  if (to < from) return;
  sheet.getRange(`A${from}:${column(last)}${to}`).format = {
    font:{name:'Arial',size:10,color:ink}, verticalAlignment:'center',wrapText:true,rowHeight:30};
  sheet.getRange(`E${from}:${column(last)}${to}`).format.horizontalAlignment='center';
}
// Worksheets are generated from the already privacy-filtered payload.
const summary = workbook.worksheets.add('Overzicht');
const detailSheets = data.lessons.map((lesson,index) => workbook.worksheets.add(`Les ${String(index+1).padStart(2,'0')} ${lesson.date.slice(8,10)}-${lesson.date.slice(5,7)}`));
const feedbackSheet = workbook.worksheets.add('Feedback');
const students = new Map();
for (const lesson of data.lessons) for (const student of lesson.students) students.set(student.key,student.name);
if (individual && students.size !== 1) throw new Error('Individual export must contain exactly one student.');
const studentList = [...students].map(([key,name])=>({key,name}));
const detailRefs = [];
const qaChecks = [];

for (const [lessonIndex, lesson] of data.lessons.entries()) {
  const sheet = detailSheets[lessonIndex];
  const lastCol = Math.max(5,4+lesson.students.length);
  const last = column(lastCol);
  base(sheet, individual ? `Puntenlijst · ${data.studentName}` : 'Puntenlijst',
    `${lesson.title} · ${lesson.subject} · ${lesson.grade ?? '?'}e leerjaar`, lastCol);
  labelRow(sheet,8,'Lesdatum');
  set(sheet,'E8',new Date(lesson.date+'T12:00:00Z'));
  sheet.getRange('E8').setNumberFormat('dd/mm/yyyy');
  header(sheet,`A11:${last}11`);
  labelRow(sheet,11,'Leerplandoelstelling / evaluatiepunt');
  for (const [i,student] of lesson.students.entries()) set(sheet,`${column(i+5)}11`,student.name);
  sheet.getRange(`A11:${last}11`).format.rowHeight=44;
  let row=12;
  const groupRefs=[];
  for (const goal of lesson.goals) {
    const titleRow=row++;
    merged(sheet,`A${titleRow}:${last}${titleRow}`,`${goal.code} · ${goal.title}`);
    sheet.getRange(`A${titleRow}:${last}${titleRow}`).format={fill:soft,font:{name:'Arial',size:10,bold:true,color:accent},wrapText:true,rowHeight:Math.max(34,Math.ceil((goal.code.length+goal.title.length)/95)*15)};
    const start=row;
    for (const point of goal.points) {
      body(sheet,row,row,lastCol);
      labelRow(sheet,row,point.title);
      sheet.getRange(`A${row}:${last}${row}`).format.rowHeight=Math.max(32,Math.ceil(point.title.length/48)*14+8);
      if (lesson.students.length) sheet.getRange(`E${row}:${last}${row}`).values=[point.values.map(v=>v===null?null:v)];
      row++;
    }
    const end=row-1;
    const total=row++, average=row++, count=row++, absent=row++;
    body(sheet,total,absent,lastCol);
    labelRow(sheet,total,'Totaal per doel'); labelRow(sheet,average,'Gemiddelde per doel');
    labelRow(sheet,count,'Aantal beoordeelde punten'); labelRow(sheet,absent,'Afwezig in opgenomen rijen');
    sheet.getRange(`A${total}:${last}${average}`).format.fill='#F8F4F6';
    sheet.getRange(`A${average}:${last}${average}`).format.font.bold=true;
    for (const [i] of lesson.students.entries()) {
      const c=column(i+5), range=`${c}${start}:${c}${end}`;
      if (end>=start) {
        formula(sheet,`${c}${count}`,`=COUNT(${range})`);
        formula(sheet,`${c}${absent}`,`=COUNTIFS(${range},"Afwezig")`);
        formula(sheet,`${c}${total}`,`=IF(${c}${count}=0,"",SUM(${range})&"/"&(${c}${count}*80))`);
        formula(sheet,`${c}${average}`,`=IF(${c}${count}=0,"",AVERAGE(${range}))`);
        const r=sheet.getRange(range);
        for (const [n,fill] of [[0,'#B91C3D'],[20,'#EF4444'],[40,'#FBBF24'],[60,'#48CA75'],[80,'#0879EF']])
          r.conditionalFormats.addCustom(`AND(ISNUMBER(${c}${start}),${c}${start}=${n})`,{fill,font:{color:n===0||n===80?'#FFFFFF':'#181818'}});
        r.conditionalFormats.add('containsText',{text:'Afwezig',format:{fill:'#E8EDF5',font:{color:'#56637A'}}});
      } else {
        set(sheet,`${c}${count}`,0);set(sheet,`${c}${absent}`,0);
      }
      sheet.getRange(`${c}${average}`).setNumberFormat('0.0');
    }
    groupRefs.push({total,average,count,absent,start,end});row++;
  }
  if (!lesson.goals.length) {labelRow(sheet,row++,'Geen ingevulde cijfers in deze les.');row++;}
  const totals={total:row++,average:row++,count:row++,absent:row++};
  body(sheet,totals.total,totals.absent,lastCol);
  labelRow(sheet,totals.total,'Algemeen totaal');labelRow(sheet,totals.average,'Algemeen gemiddelde');
  labelRow(sheet,totals.count,'Aantal beoordeelde punten');labelRow(sheet,totals.absent,'Afwezig in opgenomen rijen');
  sheet.getRange(`A${totals.total}:${last}${totals.average}`).format={fill:soft,font:{name:'Arial',size:10,bold:true,color:accent}};
  const refs = {};
  for (const [i,s] of lesson.students.entries()) {
    const c=column(i+5),sumFor=key=>groupRefs.length?`SUM(${groupRefs.map(g=>`${c}${g[key]}`).join(',')})`:'0';
    const pointRanges=groupRefs.filter(g=>g.end>=g.start).map(g=>`${c}${g.start}:${c}${g.end}`);
    const earned=pointRanges.length?`SUM(${pointRanges.join(',')})`:'0';
    formula(sheet,`${c}${totals.count}`,`=${sumFor('count')}`);
    formula(sheet,`${c}${totals.absent}`,`=${sumFor('absent')}`);
    formula(sheet,`${c}${totals.total}`,`=IF(${c}${totals.count}=0,"",${earned}&"/"&(${c}${totals.count}*80))`);
    formula(sheet,`${c}${totals.average}`,`=IF(${c}${totals.count}=0,"",${earned}/${c}${totals.count})`);
    sheet.getRange(`${c}${totals.average}`).setNumberFormat('0.0');
    refs[s.key]=Object.fromEntries(Object.entries(totals).map(([k,r])=>[k,`'${sheet.name}'!${c}${r}`]));
    const values=lesson.goals.flatMap(g=>g.points.map(p=>p.values[i])).filter(v=>typeof v==='number');
    qaChecks.push({sheet:sheet.name,cell:`${c}${totals.average}`,expected:values.length?values.reduce((a,b)=>a+b,0)/values.length:null});
    qaChecks.push({sheet:sheet.name,cell:`${c}${totals.total}`,expected:values.length?`${values.reduce((a,b)=>a+b,0)}/${values.length*80}`:null});
  }
  sheet.freezePanes.freezeRows(11);sheet.freezePanes.freezeColumns(4);
  detailRefs.push({sheet,refs,lastRow:row});
}

// Class summary is a matrix, like the source form. The individual export uses
// this same minimal grid with only the selected pupil's data, not hidden columns.
const summaryLast=Math.max(5,4+studentList.length);
base(summary,individual?`Puntenlijst per leerling · ${data.studentName}`:`Klasoverzicht · ${data.className}`,
  `${data.lessons.length} ${data.lessons.length===1?'les':'lessen'} · ${individual?'Persoonlijke resultaten':'Gemiddelde per leerling per les'}`,summaryLast);
header(summary,`A11:${column(summaryLast)}11`);
set(summary,'A11','Datum');merged(summary,'B11:D11','Les / vak');
for (const [i,s] of studentList.entries()) set(summary,`${column(i+5)}11`,s.name);
summary.getRange(`A11:${column(summaryLast)}11`).format.rowHeight=44;
let sr=12;
for (const [i,lesson] of data.lessons.entries()) {
  body(summary,sr,sr,summaryLast);set(summary,`A${sr}`,new Date(lesson.date+'T12:00:00Z'));
  summary.getRange(`A${sr}`).setNumberFormat('dd/mm/yyyy');
  merged(summary,`B${sr}:D${sr}`,`${lesson.title}\n${lesson.subject}`);
  summary.getRange(`A${sr}:${column(summaryLast)}${sr}`).format.rowHeight=Math.max(44,Math.ceil((lesson.title.length+lesson.subject.length)/34)*14+10);
  for (const [j,s] of studentList.entries()) {
    const ref=detailRefs[i].refs[s.key],cell=`${column(j+5)}${sr}`;
    if(ref) formula(summary,cell,`=IF(${ref.count}=0,"",${ref.average})`);
    else set(summary,cell,'Niet in deze les');
    summary.getRange(cell).setNumberFormat('0.0');
  }
  sr++;
}
sr++;
const summaryTotals={total:sr++,average:sr++,count:sr++,absent:sr++};
body(summary,summaryTotals.total,summaryTotals.absent,summaryLast);
for (const [key,label] of [['total','Totaal geselecteerde lessen'],['average','Gemiddelde geselecteerde lessen'],['count','Aantal beoordeelde punten'],['absent','Afwezig in opgenomen rijen']]) labelRow(summary,summaryTotals[key],label);
summary.getRange(`A${summaryTotals.total}:${column(summaryLast)}${summaryTotals.average}`).format={fill:soft,font:{name:'Arial',size:10,bold:true,color:accent}};
for (const [i,s] of studentList.entries()) {
  const c=column(i+5), refs=detailRefs.map(d=>d.refs[s.key]).filter(Boolean);
  const sum=key=>refs.length?`SUM(${refs.map(r=>r[key]).join(',')})`:'0';
  const earned=refs.length?`ROUND(SUM(${refs.map(r=>`IF(${r.count}=0,0,${r.average}*${r.count})`).join(',')}),0)`:'0';
  formula(summary,`${c}${summaryTotals.count}`,`=${sum('count')}`);
  formula(summary,`${c}${summaryTotals.absent}`,`=${sum('absent')}`);
  formula(summary,`${c}${summaryTotals.total}`,`=IF(${c}${summaryTotals.count}=0,"",${earned}&"/"&(${c}${summaryTotals.count}*80))`);
  formula(summary,`${c}${summaryTotals.average}`,`=IF(${c}${summaryTotals.count}=0,"",${earned}/${c}${summaryTotals.count})`);
  summary.getRange(`${c}${summaryTotals.average}`).setNumberFormat('0.0');
  const values=data.lessons.flatMap(lesson=>{
    const index=lesson.students.findIndex(student=>student.key===s.key);
    return index<0?[]:lesson.goals.flatMap(goal=>goal.points.map(point=>point.values[index])).filter(value=>typeof value==='number');
  });
  const total=values.reduce((a,b)=>a+b,0);
  qaChecks.push({sheet:summary.name,cell:`${c}${summaryTotals.average}`,expected:values.length?total/values.length:null});
  qaChecks.push({sheet:summary.name,cell:`${c}${summaryTotals.total}`,expected:values.length?`${total}/${values.length*80}`:null});
}
if (!individual && studentList.length) {
  sr+=2; labelRow(summary,sr,'Algemeen klasgemiddelde');
  formula(summary,`E${sr}`,`=IF(SUM(E${summaryTotals.count}:${column(summaryLast)}${summaryTotals.count})=0,"",SUMPRODUCT(E${summaryTotals.average}:${column(summaryLast)}${summaryTotals.average},E${summaryTotals.count}:${column(summaryLast)}${summaryTotals.count})/SUM(E${summaryTotals.count}:${column(summaryLast)}${summaryTotals.count}))`);
  summary.getRange(`E${sr}`).setNumberFormat('0.0');sr++;
  const values=data.lessons.flatMap(l=>l.goals.flatMap(g=>g.points.flatMap(p=>p.values))).filter(v=>typeof v==='number');
  qaChecks.push({sheet:summary.name,cell:`E${sr-1}`,expected:values.length?values.reduce((a,b)=>a+b,0)/values.length:null});
}
sr+=2;merged(summary,`A${sr}:${column(summaryLast)}${sr}`,'Deze puntenlijst bevat opgeslagen resultaten. Aanpassingen in Excel worden niet teruggeschreven naar het portaal.');
summary.getRange(`A${sr}:${column(summaryLast)}${sr}`).format={font:{name:'Arial',size:9,color:muted},wrapText:true,rowHeight:32};
summary.freezePanes.freezeRows(11);summary.freezePanes.freezeColumns(4);

base(feedbackSheet,'Feedback',individual?`Persoonlijke feedback voor ${data.studentName}`:'Klasfeedback en persoonlijke feedback per les',7);
header(feedbackSheet,'A11:G11');set(feedbackSheet,'A11','Datum');merged(feedbackSheet,'B11:C11','Les');set(feedbackSheet,'D11','Voor');merged(feedbackSheet,'E11:G11','Feedback');
feedbackSheet.getRange('A11:G11').format.rowHeight=32;
feedbackSheet.getRange('B1:C200').format.columnWidth=18;feedbackSheet.getRange('D1:D200').format.columnWidth=22;
let fr=12;
for(const lesson of data.lessons){
  const entries=[];
  if(!individual) entries.push({name:'De klas',feedback:lesson.classFeedback||''});
  entries.push(...lesson.students);
  for(const entry of entries){
    // Keep long free text complete, with manageable row heights.
    const message=entry.feedback || 'Geen feedback ingevuld.';
    const chunks=message.match(/[\s\S]{1,600}/g) || [''];
    for(const [index,chunk] of chunks.entries()){
      body(feedbackSheet,fr,fr,7);
      set(feedbackSheet,`A${fr}`,new Date(lesson.date+'T12:00:00Z'));feedbackSheet.getRange(`A${fr}`).setNumberFormat('dd/mm/yyyy');
      merged(feedbackSheet,`B${fr}:C${fr}`,lesson.title);set(feedbackSheet,`D${fr}`,entry.name);
      merged(feedbackSheet,`E${fr}:G${fr}`,chunk);
      feedbackSheet.getRange(`B${fr}:G${fr}`).format.horizontalAlignment='left';
      feedbackSheet.getRange(`A${fr}:G${fr}`).format.verticalAlignment='top';
      const lines=Math.max(Math.ceil(lesson.title.length/30),Math.ceil(entry.name.length/20),chunk.split('\n').reduce((n,s)=>n+Math.max(1,Math.ceil(s.length/60)),0));
      feedbackSheet.getRange(`A${fr}:G${fr}`).format.rowHeight=Math.max(42,lines*15+12);
      fr++;
    }
  }
}
feedbackSheet.freezePanes.freezeRows(11);
workbook.recalculate();
for(const check of qaChecks){
  const value=workbook.worksheets.getItem(check.sheet).getRange(check.cell).values[0][0];
  if(check.expected===null ? (value!==null && value!=='') : typeof check.expected==='string' ? value!==check.expected : (typeof value!=='number'||Math.abs(value-check.expected)>1e-8))
    throw new Error(`Calculation verification failed at ${check.sheet}!${check.cell}`);
}
const errors=await workbook.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:2000});
if(previewPath){
  await fs.mkdir(previewPath,{recursive:true});
  for(const [sheet,lastRow,lastCol] of [[summary,sr,summaryLast],...detailRefs.map(d=>[d.sheet,d.lastRow,Math.max(5,4+data.lessons[detailRefs.indexOf(d)].students.length)]),[feedbackSheet,fr-1,7]]){
    const preview=await workbook.render({sheetName:sheet.name,range:`A1:${column(lastCol)}${lastRow}`,scale:1,format:'png'});
    await fs.writeFile(path.join(previewPath,`${sheet.name}.png`),new Uint8Array(await preview.arrayBuffer()));
  }
  await fs.writeFile(path.join(previewPath,'checks.json'),JSON.stringify({averages:qaChecks,errorScan:errors.ndjson},null,2));
}
await fs.mkdir(path.dirname(outputPath),{recursive:true});
const output=await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(JSON.stringify({ok:true,sheets:detailSheets.length+2,mode:data.mode}));
