(function(root){
  'use strict';
  function validate(data){
    if(!data||data.schema_version!=='hardcad.comparison.v1'||!Array.isArray(data.requirements)||!data.requirements.length||data.requirements.length>5000)throw Error('hardcad.comparison.v1 / requirements');
    const ids=new Set(),statuses=new Set(['PASS','FAIL','UNDETERMINED','ERROR']);
    for(const row of data.requirements){
      if(!row||typeof row.id!=='string'||!row.id||row.id.length>256||ids.has(row.id)||typeof row.unit!=='string'||row.unit.length>32||!statuses.has(row.before_status)||!statuses.has(row.after_status))throw Error('invalid requirement');
      ids.add(row.id);
      for(const field of ['before_value','after_value','measured_delta']){const value=row[field];if(value!==null&&(typeof value!=='number'||!Number.isFinite(value)))throw Error('invalid measurement');}
      for(const side of ['before','after']){const measured=['PASS','FAIL'].includes(row[side+'_status']);if(measured!==(row[side+'_value']!==null))throw Error('measurement status mismatch');}
      if((!['PASS','FAIL'].includes(row.before_status)||!['PASS','FAIL'].includes(row.after_status))&&row.measured_delta!==null)throw Error('unmeasured delta');
    }
    return data;
  }
  const api={validate};if(typeof module==='object'&&module.exports)module.exports=api;else root.HardCadComparison=api;
})(typeof globalThis==='object'?globalThis:this);
