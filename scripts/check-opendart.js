// Opt-in live smoke check. Never prints API keys, request URLs or raw error messages.
import {createAdapter,COMPANIES} from '../server/opendart.js';
if(!process.env.OPENDART_API_KEY){console.error('Live test skipped: configure a newly issued OPENDART_API_KEY in the server environment.');process.exitCode=2;}
else {
 const adapter=createAdapter();
 for(const [id,company] of Object.entries(COMPANIES)) {
  const data=await adapter.financials({id,year:String(new Date().getUTCFullYear()-1),reportCode:'11011',fsDiv:'CFS'});
  console.log(JSON.stringify({id,name:company.name,status:data.status,reason:data.missing_reason,asOf:data.observed_at,filedAt:data.available_at,metrics:data.metrics.filter(m=>m.value!==null).length}));
  if(data.status!=='ok')process.exitCode=1;
 }
}
