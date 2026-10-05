"""Standalone XLSX renderer. No Node.js or Codex runtime is required."""
from datetime import datetime
from io import BytesIO
from pathlib import Path
import math
import struct
import zlib
import textwrap
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell as cell, xl_col_to_name as column


def build_workbook(data, logo_path):
    stream = BytesIO()
    book = xlsxwriter.Workbook(stream, {'in_memory': True, 'strings_to_formulas': False,
                                      'strings_to_urls': False})
    accent, soft = '#B80045', '#F5E8EE'
    def fmt(**options):
        return book.add_format({'font_name':'Arial','font_size':10,'font_color':'#27252B',
                                'valign':'vcenter','text_wrap':True,'border':1,'border_color':'#D6DEE8', **options})
    normal, numeric = fmt(), fmt(align='center')
    average_fmt = fmt(align='center', num_format='0.0', bold=True)
    heading = fmt(bg_color='#DCE7F5',font_color='#294E70',bold=True,align='left')
    student_heading = fmt(bg_color='#DCE7F5',font_color='#294E70',bold=True,align='center',rotation=90,font_size=10)
    section = fmt(bg_color=soft,font_color=accent,bold=True)
    total_fmt = fmt(bg_color=soft,font_color=accent,bold=True,align='center',num_format='0.0"/100"')
    date_fmt = fmt(num_format='dd/mm/yyyy',align='left')
    muted = fmt(font_size=9,font_color='#6E6570')
    individual = data['mode'] == 'student'
    students = {s['key']:s['name'] for lesson in data['lessons'] for s in lesson['students']}
    if individual and len(students) != 1:
        raise ValueError('Een individuele puntenlijst moet precies één leerling bevatten.')
    summary = book.add_worksheet('Puntenlijst leerling' if individual else 'Klasoverzicht evaluaties')
    details = [book.add_worksheet(f"Les {i+1:02d} {lesson['date'][8:10]}-{lesson['date'][5:7]}")
               for i,lesson in enumerate(data['lessons'])]
    feedback = book.add_worksheet('Feedback')

    def merge(sheet,row,start,end,value,style=normal):
        sheet.merge_range(row,start,row,end,value,style)

    def label(sheet,row,value,style=normal):
        merge(sheet,row,0,3,value,style)

    def header_logo(path):
        # Physical PNG resolution only: original logo pixels remain unchanged.
        raw=Path(path).read_bytes()
        if raw[:8] != b'\x89PNG\r\n\x1a\n': return BytesIO(raw)
        width,height=struct.unpack('>II',raw[16:24])
        ppm=round(max(width/150,height/28)*96/.0254)
        payload=struct.pack('>IIB',ppm,ppm,1)
        chunk=struct.pack('>I',9)+b'pHYs'+payload+struct.pack('>I',zlib.crc32(b'pHYs'+payload)&0xffffffff)
        parts=[raw[:8]];offset=8
        while offset<len(raw):
            size=struct.unpack('>I',raw[offset:offset+4])[0];kind=raw[offset+4:offset+8]
            if kind!=b'pHYs':parts.append(raw[offset:offset+size+12])
            if kind==b'IHDR':parts.append(chunk)
            offset+=size+12
        return BytesIO(b''.join(parts))

    def escape(value): return str(value).replace('&','&&').replace('\n',' ')

    def base(sheet,title,subtitle,last,lesson=None):
        sheet.hide_gridlines(2);sheet.set_tab_color(accent)
        sheet.set_landscape();sheet.set_paper(9);sheet.fit_to_pages(1,0)
        sheet.set_margins(.7,.7,.75,.75)
        sheet.repeat_rows(10,10);sheet.freeze_panes(11,4)
        sheet.set_column(0,0,12,normal)
        text_width=max(36,132-max(1,last-3)*7)
        sheet.set_column(1,3,text_width/3,normal)
        sheet.set_column(4,last,7,numeric)
        sheet.set_default_row(25)
        for row in range(10):sheet.set_row(row,0,options={'hidden':True})
        chosen=[lesson] if lesson else data['lessons']
        subject=' / '.join(dict.fromkeys(l['subject'] for l in chosen))
        teachers=', '.join(dict.fromkeys(l.get('teacher','') for l in chosen))
        grade=lesson.get('grade') if lesson else data.get('grade')
        head=f'&L&G&C&"Arial,Bold"&10&K294E70&A\n&9{escape(subject)[:65]}&R&"Arial,Regular"&8&K586B80{escape(data["direction"])[:65]}\n{grade or "?"}e leerjaar'
        foot=f'&L&"Arial,Regular"&7&K586B80{escape(data["schoolYear"])} · {escape(data["className"])}\n{escape(teachers)[:65]}&C&7&K586B80&P / &N&R&7&K586B80Scores: 0 / 20 / 40 / 60 / 80.\nLeeg en Afwezig tellen niet mee; 0 wel.\nTotaal op 100; gemiddelde op 80.'
        sheet.set_header(head,{'image_left':str(logo_path),'image_data_left':header_logo(logo_path),'margin':.3})
        sheet.set_footer(foot,{'margin':.3})
        sheet.print_area(10,0,10,last)

    palette=[(0,'#B91C3D'),(20,'#EF4444'),(40,'#FBBF24'),(60,'#48CA75'),(80,'#0879EF')]
    def color_average(sheet,row,col,reference=None):
        ref=reference or cell(row,col)
        for low,fill in reversed(palette):
            sheet.conditional_format(row,col,row,col,{'type':'formula','criteria':f'=AND(ISNUMBER({ref}),{ref}>={low},{ref}<{low+20})','format':fmt(bg_color=fill,font_color='white' if low in (0,80) else '#181818')})

    def stripe(sheet,start,end,last):
        if end>=start:
            sheet.conditional_format(start,0,end,last,{'type':'formula','criteria':'=MOD(ROW(),2)=0','format':book.add_format({'bg_color':'#F1F5FA'})})

    def names(sheet,learners):
        sheet.set_row(10,105)
        for i,name in enumerate(learners):
            parts=textwrap.wrap(name,18,break_long_words=False,break_on_hyphens=False)
            sheet.write_string(10,i+4,'\n'.join(parts),student_heading)

    def stats(values):
        numbers=[v for v in values if isinstance(v,int)]
        return {'count':len(numbers),'sum':sum(numbers),
                'average':sum(numbers)/len(numbers) if numbers else '',
                'total':sum(numbers)/(len(numbers)*80)*100 if numbers else '',
                'absent':values.count('Afwezig')}

    def write_totals(sheet,row,entries,formulas,labels):
        positions={key:row+i for i,(key,_) in enumerate(labels)}
        for key,title in labels:
            label(sheet,positions[key],title,section if key in ('total','average') else normal)
        for index,values in enumerate(entries):
            metrics=stats(values);col=index+4
            for key,_ in labels:
                style=average_fmt if key=='average' else total_fmt if key=='total' else numeric
                sheet.write_formula(positions[key],col,formulas(index,positions,key),style,metrics[key])
                if key in ('total','average'):color_average(sheet,positions[key],col,cell(positions['average'],col))
        return positions

    labels=[('total','Algemeen totaal'),('average','Algemeen gemiddelde'),
            ('count','Aantal beoordeelde punten'),('absent','Afwezig in opgenomen rijen')]
    detail_refs=[]
    for lesson,sheet in zip(data['lessons'],details):
        last=max(4,3+len(lesson['students']))
        base(sheet,f"Puntenlijst · {data['studentName']}" if individual else 'Puntenlijst',
             f"{lesson['title']} · {lesson['subject']} · {lesson['grade'] or '?'}e leerjaar",last,lesson)
        merge(sheet,9,0,last,f"{lesson['date']} · {lesson['title']}",section)
        sheet.set_row(9,32,options={'hidden':False})
        sheet.repeat_rows(9,10)
        label(sheet,10,'Leerplandoelstelling / evaluatiepunt',heading)
        names(sheet,[s['name'] for s in lesson['students']])
        row=11; ranges=[]
        all_values=[[] for s in lesson['students']]
        for goal in lesson['goals']:
            merge(sheet,row,0,last,f"{goal['code']} · {goal['title']}",fmt(bg_color='#EAD9F1',font_color='#6B286D',bold=True,top=2,top_color='#B687BF'))
            sheet.set_row(row,max(34,math.ceil((len(goal['code'])+len(goal['title']))/95)*15))
            row+=1;start=row
            entries=[[] for s in lesson['students']]
            for point in goal['points']:
                label(sheet,row,point['title'])
                sheet.set_row(row,max(32,math.ceil(len(point['title'])/48)*14+8))
                for i,value in enumerate(point['values']):
                    sheet.write(row,i+4,value,numeric)
                    entries[i].append(value);all_values[i].append(value)
                row+=1
            end=row-1
            if end<start:continue
            ranges.append((start,end))
            for i in range(len(lesson['students'])):
                col=i+4;ref=cell(start,col)
                for number,fill in [(0,'#B91C3D'),(20,'#EF4444'),(40,'#FBBF24'),(60,'#48CA75'),(80,'#0879EF')]:
                    sheet.conditional_format(start,col,end,col,{'type':'formula','criteria':f'=AND(ISNUMBER({ref}),{ref}={number})',
                        'format':fmt(bg_color=fill,font_color='white' if number in (0,80) else '#181818')})
                sheet.conditional_format(start,col,end,col,{'type':'text','criteria':'containing','value':'Afwezig',
                    'format':fmt(bg_color='#E8EDF5',font_color='#56637A')})
            def goal_formula(i,positions,key):
                ref=f'{cell(start,i+4)}:{cell(end,i+4)}';count=cell(positions['count'],i+4)
                return {'count':f'=COUNT({ref})','absent':f'=COUNTIFS({ref},"Afwezig")',
                    'total':f'=IF({count}=0,"",SUM({ref})/({count}*80)*100)',
                    'average':f'=IF({count}=0,"",AVERAGE({ref}))'}[key]
            write_totals(sheet,row,entries,goal_formula,[('total','Totaal per doel'),('average','Gemiddelde per doel'),*labels[2:]])
            stripe(sheet,start,end,last)
            for col in range(last+1): sheet.write_blank(row+4,col,None,fmt(border=0))
            sheet.set_row(row+4,10)
            row+=5
        if not ranges:label(sheet,row,'Geen ingevulde cijfers in deze les.');row+=2
        def lesson_formula(i,positions,key):
            refs=[f'{cell(start,i+4)}:{cell(end,i+4)}' for start,end in ranges]
            total=f'SUM({",".join(refs)})' if refs else '0'
            count=cell(positions['count'],i+4)
            absence='+'.join(f'COUNTIFS({r},"Afwezig")' for r in refs) or '0'
            return {'count':f'=COUNT({",".join(refs)})' if refs else '=0','absent':f'={absence}',
                'total':f'=IF({count}=0,"",{total}/({count}*80)*100)',
                'average':f'=IF({count}=0,"",{total}/{count})'}[key]
        positions=write_totals(sheet,row,all_values,lesson_formula,labels)
        sheet.print_area(9,0,row+3,last)
        detail_refs.append({s['key']:{key:f"'{sheet.name}'!{cell(r,i+4)}" for key,r in positions.items()}
                            for i,s in enumerate(lesson['students'])})

    last=max(4,3+len(students))
    base(summary,f"Puntenlijst per leerling · {data['studentName']}" if individual else f"Klasoverzicht · {data['className']}",
         f"{len(data['lessons'])} lessen · Gemiddelde per leerling per les",last)
    summary.write_string(10,0,'Datum',heading);merge(summary,10,1,3,'Lesonderwerp',heading)
    names(summary,students.values())
    row=11
    for lesson,refs in zip(data['lessons'],detail_refs):
        summary.write_datetime(row,0,datetime.fromisoformat(lesson['date']),date_fmt)
        merge(summary,row,1,3,lesson['title'])
        summary.set_row(row,max(44,math.ceil((len(lesson['title'])+len(lesson['subject']))/34)*14+10))
        for i,key in enumerate(students):
            if key not in refs:summary.write_string(row,i+4,'Niet in deze les',numeric);continue
            learner=next(index for index,s in enumerate(lesson['students']) if s['key']==key)
            values=[p['values'][learner] for g in lesson['goals'] for p in g['points']]
            summary.write_formula(row,i+4,f'=IF({refs[key]["count"]}=0,"",{refs[key]["average"]})',average_fmt,stats(values)['average'])
            color_average(summary,row,i+4)
        row+=1
    stripe(summary,11,row-1,last)
    row+=1;entries=[]
    for key in students:
        values=[]
        for lesson in data['lessons']:
            for index,s in enumerate(lesson['students']):
                if s['key']==key:values.extend(p['values'][index] for g in lesson['goals'] for p in g['points'])
        entries.append(values)
    def summary_formula(i,positions,key):
        student_key=list(students)[i];refs=[r[student_key] for r in detail_refs if student_key in r]
        count=cell(positions['count'],i+4)
        def add(field):return 'SUM('+','.join(r[field] for r in refs)+')' if refs else '0'
        earned='ROUND(SUM('+','.join(f'IF({r["count"]}=0,0,{r["average"]}*{r["count"]})' for r in refs)+'),0)' if refs else '0'
        return {'count':'='+add('count'),'absent':'='+add('absent'),
                'total':f'=IF({count}=0,"",{earned}/({count}*80)*100)',
                'average':f'=IF({count}=0,"",{earned}/{count})'}[key]
    positions=write_totals(summary,row,entries,summary_formula,[('total','Totaal geselecteerde lessen'),('average','Gemiddelde geselecteerde lessen'),*labels[2:]])
    row+=4
    if not individual and students:
        label(summary,row,'Algemeen klasgemiddelde')
        count=f'E{positions["count"]+1}:{column(last)}{positions["count"]+1}'
        average=f'E{positions["average"]+1}:{column(last)}{positions["average"]+1}'
        summary.write_formula(row,4,f'=IF(SUM({count})=0,"",SUMPRODUCT({average},{count})/SUM({count}))',average_fmt,stats([v for entry in entries for v in entry])['average'])
        color_average(summary,row,4)
        row+=1
    merge(summary,row,0,last,'Deze puntenlijst bevat opgeslagen resultaten. Aanpassingen in Excel worden niet teruggeschreven naar het portaal.',muted)
    summary.set_row(row,32)
    summary.print_area(10,0,row,last)

    base(feedback,'Feedback',f"Persoonlijke feedback voor {data['studentName']}" if individual else 'Klasfeedback en persoonlijke feedback per les',6)
    feedback.set_column(1,2,16,normal);feedback.set_column(3,3,22,normal);feedback.set_column(4,6,24,normal)
    feedback.set_row(10,25)
    feedback.write_string(10,0,'Datum',heading);merge(feedback,10,1,2,'Les',heading)
    feedback.write_string(10,3,'Voor',heading);merge(feedback,10,4,6,'Feedback',heading)
    row=11
    for lesson in data['lessons']:
        entries=lesson['students'] if individual else [{'name':'De klas','feedback':lesson.get('classFeedback','')},*lesson['students']]
        for entry in entries:
            message=entry['feedback'] or 'Geen feedback ingevuld.'
            for offset in range(0,len(message),600):
                chunk=message[offset:offset+600]
                feedback.write_datetime(row,0,datetime.fromisoformat(lesson['date']),date_fmt)
                merge(feedback,row,1,2,lesson['title']);feedback.write_string(row,3,entry['name'],normal)
                merge(feedback,row,4,6,chunk)
                lines=max(math.ceil(len(lesson['title'])/30),math.ceil(len(entry['name'])/20),sum(max(1,math.ceil(len(line)/60)) for line in chunk.split('\n')))
                feedback.set_row(row,max(42,lines*15+12));row+=1
    stripe(feedback,11,row-1,6)
    feedback.print_area(10,0,max(11,row-1),6)
    book.close()
    return stream.getvalue()
