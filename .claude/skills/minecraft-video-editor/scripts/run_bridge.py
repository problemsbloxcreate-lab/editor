import json,os,sys,time,uuid
from pathlib import Path
helpers=r'''
function __quote(s){return '"'+String(s).replace(/\\/g,'\\\\').replace(/"/g,'\\"').replace(/\r/g,'\\r').replace(/\n/g,'\\n').replace(/\t/g,'\\t').replace(/[\x00-\x1f]/g,function(c){return '\\u'+('0000'+c.charCodeAt(0).toString(16)).slice(-4);})+'"';}
function __json(x){if(x===null||typeof x==='undefined')return 'null';if(typeof x==='string')return __quote(x);if(typeof x==='number')return isFinite(x)?String(x):'null';if(typeof x==='boolean')return x?'true':'false';var a=[];if(x instanceof Array){for(var i=0;i<x.length;i++)a.push(__json(x[i]));return '['+a.join(',')+']';}for(var k in x)if(x.hasOwnProperty(k))a.push(__quote(k)+':'+__json(x[k]));return '{'+a.join(',')+'}';}
function __result(x){return __json({success:true,data:x});}
function __error(x){return __json({success:false,error:String(x)});}
'''
path=Path(sys.argv[1]); code=path.read_text(encoding='utf-8'); timeout=float(sys.argv[2]) if len(sys.argv)>2 else 30
folder=Path(os.environ['TEMP'])/'premiere-mcp-bridge'; folder.mkdir(exist_ok=True)
uid=uuid.uuid4().hex; cmd=folder/f'cmd_{uid}.jsx'; response=folder/f'res_{uid}.json'
cmd.write_text(helpers+'\n(function(){try{\n'+code+'\n}catch(e){return __error(e.toString());}})();',encoding='utf-8')
try:
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if response.exists():
            try:data=json.loads(response.read_text(encoding='utf-8'))
            except (OSError,ValueError):time.sleep(.2);continue
            if not data.get('success'):raise RuntimeError(str(data.get('error')))
            result=data.get('data');path.with_suffix('.result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps(result,ensure_ascii=True)[:6000]);break
        time.sleep(.2)
    else:raise TimeoutError('Premiere MCP Bridge did not respond')
finally:
    cmd.unlink(missing_ok=True);response.unlink(missing_ok=True)
