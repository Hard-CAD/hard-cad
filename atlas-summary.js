Object.assign(extra.en,{inspectLink:'3D comparison studio ↗'});
Object.assign(extra.zh,{inspectLink:'三维对比与报告导入 ↗'});
Object.assign(extra.ja,{inspectLink:'3D 比較・レポート読込 ↗'});
Object.assign(extra.ko,{inspectLink:'3D 비교 및 보고서 가져오기 ↗'});
Object.assign(extra.en,{replayLink:'Interactive evidence replay ↗'});
Object.assign(extra.zh,{replayLink:'交互式证据回放 ↗'});
Object.assign(extra.ja,{replayLink:'実験結果のインタラクティブ再生 ↗'});
Object.assign(extra.ko,{replayLink:'인터랙티브 근거 재생 ↗'});
Object.assign(extra.en,{pumpDemoLink:'Process pump demo ↗'});
Object.assign(extra.zh,{pumpDemoLink:'工艺流程泵 3D 演示 ↗'});
Object.assign(extra.ja,{pumpDemoLink:'プロセスポンプ 3D デモ ↗'});
Object.assign(extra.ko,{pumpDemoLink:'공정 펌프 3D 데모 ↗'});

const landscapeLabels={en:'Related work',zh:'相关研究',ja:'関連研究',ko:'관련 연구'};
const landscapeSummary={
 en:['Prior studies examine CAD geometry and features, executable tests, design constraints, interfaces, and preservation across edits.','Hard-CAD connects declared requirements to paired measurements, availability and local/global changes in a replayable record.'],
 zh:['相关研究分别关注 CAD 几何与特征、可执行测试、设计约束、装配接口，以及修改过程中的几何保持。','Hard-CAD 将声明的要求与修改前后的配对测量、可用状态及局部和整体变化连接到可重放记录。'],
 ja:['関連研究は CAD の形状・特徴、実行可能な検査、設計制約、接合部、変更時の形状保持をそれぞれ扱います。','Hard-CAD は明示された要件に変更前後の測定、測定可能性、局所・全体の変化を結び付け、再実行できる記録にします。'],
 ko:['관련 연구는 CAD 형상과 특징, 실행 가능한 검사, 설계 제약, 접합부, 수정 과정의 형상 보존을 각각 다룹니다.','Hard-CAD는 명시된 요구사항에 수정 전후 측정값, 측정 가능 여부, 국소·전체 변화를 연결해 재실행 가능한 기록으로 남깁니다.']
};
for(const lang of Object.keys(landscapeSummary))atlasCopy[lang].hard=landscapeSummary[lang];
const landscapeShowResearch=showResearch;showResearch=function(key){landscapeShowResearch(key);if(key==='hard')document.querySelector('#atlas-other-label').textContent=landscapeLabels[locale];};
const landscapeSetLocale=setLocale;setLocale=function(lang){landscapeSetLocale(lang);showResearch(activeResearch);};setLocale(locale);
