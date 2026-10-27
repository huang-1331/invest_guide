import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve,sep,extname} from 'node:path';
import {createAdapter,validateQuery,unavailable} from './opendart.js';
const root=resolve(fileURLToPath(new URL('../dist/',import.meta.url)));
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'};
export function createApp({adapter=createAdapter()}={}) {
  return createServer(async(req,res)=>{
    res.setHeader('X-Content-Type-Options','nosniff');
    res.setHeader('Referrer-Policy','no-referrer');
    const json=(code,body)=>{res.writeHead(code,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(JSON.stringify(body));};
    try {
      const url=new URL(req.url,'http://localhost');
      if(req.method!=='GET'&&req.method!=='HEAD') {res.setHeader('Allow','GET, HEAD');return json(405,{error:'method_not_allowed'});}
      if(url.pathname.startsWith('/api/')) {
        const match=url.pathname.match(/^\/api\/companies\/(\d{6})\/financials$/);
        if(!match)return json(404,unavailable('not_found'));
        const params=validateQuery(match[1],url.searchParams);
        if(params.error)return json(params.httpStatus,unavailable(params.error));
        return json(200,await adapter.financials(params));
      }
      const path=resolve(root,'.'+decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname));
      // Only serve the public dist assets. Never expose env, source, tests or Git history.
      if(!path.startsWith(root+sep)||!types[extname(path)])return json(404,{error:'not_found'});
      const content=await readFile(path);
      res.writeHead(200,{'Content-Type':types[extname(path)],'Cache-Control':'no-cache'});
      res.end(req.method==='HEAD'?undefined:content);
    }catch(error){json(error.code==='ENOENT'?404:500,{error:error.code==='ENOENT'?'not_found':'server_error'});}
  });
}
if(process.argv[1]===fileURLToPath(import.meta.url)) {
  const server=createApp();
  server.listen(Number(process.env.PORT)||4173,process.env.HOST||'127.0.0.1',()=>console.log(`Invest guide server listening on port ${server.address().port}`));
}
