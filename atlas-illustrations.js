/* Research-position diagrams are original schematic illustrations. */
const atlasCopy = {
  en: {caption:'Conceptual illustration · drawn for this website, not reproduced from the selected paper',heading:'Contribution positioning',diagram:'Conceptual diagram',
    bench:['Evaluates CAD programs with geometric, feature and edit-related measures.','Binds a declared requirement to paired local measurements and global material changes.'],
    tests:['Executes prompt-specific geometry and topology checks, with test feedback.','Retains requirement identity, measurement availability and revision-to-revision change in a replayable record.'],
    cit:['Organizes inferred constraints and verifies edits against design intent.','Uses declared operands and a common contract to interpret paired measurements under fixed checking conditions.'],
    gen:['Evaluates mating interfaces with declared keep-in and keep-out geometry.','Records empty-region occupancy across revisions; the paper compares one fixed-pose component, not the full benchmark.'],
    trace:['Combines repair memory and localized search with geometry-preservation measures.','Connects local requirement identity and state transitions to global material changes and replay.'],
    hard:['A contract specifies the source, entities, frame, units, state or path, operator and bound.','Pairs the same declared requirement, keeps availability explicit, and binds local/global evidence to executable replay.'],
    future:['The paper proposes independently specified entity, feature and state references, and controlled repair comparisons.','The present work supplies a diagnostic schema and replayable records as a basis for those future studies.']},
  zh: {caption:'网页原创概念示意图 · 非所选论文原图',heading:'贡献定位对照',diagram:'概念示意图',
    bench:['以几何、特征和修改相关指标评估 CAD 程序。','将声明的要求绑定到配对的局部测量及整体材料变化。'],
    tests:['执行针对提示的几何和拓扑检查，并使用测试反馈。','在可重放的记录中保留要求标识、测量可用性及修订前后变化。'],
    cit:['组织推断的约束，并依据设计意图验证修改。','使用声明的对象与共同契约，解释固定检查条件下的配对测量。'],
    gen:['使用声明的保留和禁入几何评估装配接口。','记录修订前后的空区占据；论文比较的是一个固定姿态组件，而非完整基准。'],
    trace:['结合修复记忆、局部搜索和几何保持指标。','将局部要求标识与状态变化连接到整体材料变化和重放。'],
    hard:['契约明确来源、对象、坐标系、单位、状态或路径、算子与边界。','配对同一声明要求，保留可用状态，并将局部及整体证据绑定到可执行重放。'],
    future:['论文提出独立指定实体、特征和状态参考，并开展受控的修复比较。','当前工作提供诊断模式与可重放记录，为这些后续研究奠定基础。']},
  ja: {caption:'本サイト独自の概念図 · 選択した論文の図の転載ではありません',heading:'研究上の位置付け',diagram:'概念図',
    bench:['幾何、特徴、編集に関する指標で CAD プログラムを評価します。','宣言された要件を、対応する局所測定と全体の材料変化に結び付けます。'],
    tests:['プロンプトに応じた幾何・位相テストを実行し、結果をフィードバックに用います。','要件 ID、測定可能性、修訂間の変化を再実行可能な記録に保持します。'],
    cit:['推定された制約を整理し、設計意図に照らして編集を検証します。','宣言された対象と共通契約を用い、固定条件下の対応する測定を解釈します。'],
    gen:['保持・禁止領域を用いて接合面を評価します。','修訂間の空領域占有を記録します。論文の比較対象は固定姿勢の一コンポーネントです。'],
    trace:['修復メモリ、局所探索、形状保持指標を組み合わせます。','局所要件の ID と状態遷移を全体材料の変化と再実行に結び付けます。'],
    hard:['契約は出典、対象、座標系、単位、状態または経路、演算、境界を指定します。','同じ要件を対応付け、可用性を明示し、局所・全体の証拠を再実行に結び付けます。'],
    future:['独立に指定された実体・特徴・状態の参照と統制された修復比較を提案しています。','現在の研究は、その基礎として診断スキーマと再実行可能な記録を提供します。']},
  ko: {caption:'웹사이트에서 제작한 개념도 · 선택한 논문의 원본 그림이 아닙니다',heading:'기여의 위치 비교',diagram:'개념도',
    bench:['형상, 특징 및 편집 관련 지표로 CAD 프로그램을 평가합니다.','선언된 요구사항을 쌍별 국소 측정과 전체 재료 변화에 연결합니다.'],
    tests:['프롬프트별 형상·위상 검사를 실행하고 그 결과를 피드백에 사용합니다.','요구사항 ID, 측정 가능 여부 및 수정 간 변화를 재실행 가능한 기록으로 보존합니다.'],
    cit:['추론된 제약을 구성하고 설계 의도에 따라 편집을 검증합니다.','선언된 대상과 공통 계약을 사용해 고정 조건의 쌍별 측정을 해석합니다.'],
    gen:['지정된 유지·금지 영역으로 접합 인터페이스를 평가합니다.','수정 간 빈 영역 점유를 기록합니다. 논문은 전체 벤치마크가 아닌 고정 자세의 구성 요소를 비교합니다.'],
    trace:['수정 메모리와 국소 탐색을 형상 보존 지표와 결합합니다.','국소 요구사항 ID와 상태 전이를 전체 재료 변화 및 재실행에 연결합니다.'],
    hard:['계약은 출처, 대상, 좌표계, 단위, 상태 또는 경로, 연산 및 경계를 지정합니다.','같은 요구사항을 짝짓고 가용성을 명시하며 국소·전체 증거를 재실행에 연결합니다.'],
    future:['논문은 독립적으로 지정된 개체·특징·상태 참조와 통제된 수정 비교를 제안합니다.','현재 연구는 후속 연구의 기반으로 진단 스키마와 재실행 가능한 기록을 제공합니다.']}
};
const diagramWords = {
  en:{candidate:'candidate',reference:'reference',tests:'checks',intent:'intent',constraints:'constraints',keepIn:'keep-in',keepOut:'keep-out',before:'before',after:'after',history:'history',contract:'contract',measure:'measure',replay:'replay',binding:'binding',repair:'repair',physics:'physics'},
  zh:{candidate:'候选',reference:'参考',tests:'检查',intent:'意图',constraints:'约束',keepIn:'保留区',keepOut:'禁入区',before:'修改前',after:'修改后',history:'历史',contract:'契约',measure:'测量',replay:'重放',binding:'绑定',repair:'修复',physics:'物理'},
  ja:{candidate:'候補',reference:'参照',tests:'検査',intent:'意図',constraints:'制約',keepIn:'保持域',keepOut:'禁止域',before:'変更前',after:'変更後',history:'履歴',contract:'契約',measure:'測定',replay:'再実行',binding:'対応付け',repair:'修復',physics:'物理'},
  ko:{candidate:'후보',reference:'참조',tests:'검사',intent:'의도',constraints:'제약',keepIn:'유지 영역',keepOut:'금지 영역',before:'수정 전',after:'수정 후',history:'이력',contract:'계약',measure:'측정',replay:'재실행',binding:'연결',repair:'수정',physics:'물리'}
};
const diagramSVG = {
 bench:w=>`<rect x="39" y="40" width="116" height="104" rx="9" class="diag-teal"/><rect x="96" y="58" width="116" height="104" rx="9" class="diag-purple"/><circle cx="157" cy="109" r="20" class="diag-hole"/><path d="M156 76v66M123 109h66" class="diag-dash"/><text x="48" y="28">${w.reference}</text><text x="149" y="181">${w.candidate}</text><text x="214" y="40" class="diag-mark">IoU</text>`,
 tests:w=>`<rect x="58" y="21" width="132" height="156" rx="8" class="diag-page"/><path d="M75 50h11v11H75z M75 79h11v11H75z M75 108h11v11H75z" class="diag-box"/><path d="m77 54 3 3 5-6 M77 83l3 3 5-6" class="diag-check"/><path d="M100 56h67M100 85h67M100 114h47" class="diag-line"/><circle cx="196" cy="143" r="27" class="diag-purple"/><path d="m185 143 8 8 15-18" class="diag-check"/><text x="90" y="154">${w.tests}</text>`,
 cit:w=>`<rect x="100" y="20" width="98" height="32" rx="6" class="diag-purple"/><text x="149" y="41" text-anchor="middle">${w.intent}</text><path d="M149 53v27M56 80h186M56 80v26M149 80v26M242 80v26" class="diag-wire"/><rect x="22" y="107" width="68" height="38" rx="5" class="diag-teal"/><rect x="115" y="107" width="68" height="38" rx="5" class="diag-teal"/><rect x="208" y="107" width="68" height="38" rx="5" class="diag-teal"/><text x="149" y="171" text-anchor="middle">${w.constraints}</text>`,
 gen:w=>`<path d="M62 49 139 19l96 38-76 30z" class="diag-top"/><path d="M62 49v94l97 38V87z" class="diag-front"/><path d="M159 87v94l76-38V57z" class="diag-side"/><ellipse cx="157" cy="83" rx="40" ry="21" class="diag-void"/><rect x="119" y="77" width="76" height="54" rx="24" class="diag-keepout"/><path d="M85 35h45 M85 35v-8 M202 151h40 M242 151v-8" class="diag-wire"/><text x="53" y="25">${w.keepIn}</text><text x="202" y="174">${w.keepOut}</text>`,
 trace:w=>`<path d="M44 93H255" class="diag-wire"/><circle cx="61" cy="93" r="19" class="diag-teal"/><circle cx="149" cy="93" r="19" class="diag-purple"/><circle cx="237" cy="93" r="19" class="diag-teal"/><path d="m57 93 4 4 7-9 M145 93l4 4 7-9 M233 93l4 4 7-9" class="diag-check"/><path d="M61 75V45h87 M149 112v30h88" class="diag-dash"/><text x="61" y="133" text-anchor="middle">${w.before}</text><text x="237" y="133" text-anchor="middle">${w.after}</text><text x="149" y="37" text-anchor="middle">${w.history}</text>`,
 hard:w=>`<rect x="17" y="67" width="73" height="58" rx="5" class="diag-page"/><path d="M30 83h45 M30 94h45 M30 105h29" class="diag-line"/><rect x="111" y="45" width="65" height="60" rx="5" class="diag-teal"/><rect x="137" y="76" width="65" height="60" rx="5" class="diag-purple"/><path d="M92 96h16 M205 106h26" class="diag-wire"/><rect x="231" y="68" width="52" height="70" rx="5" class="diag-page"/><path d="M241 86h32 M241 97h32 M241 108h23" class="diag-line"/><text x="53" y="150" text-anchor="middle">${w.contract}</text><text x="157" y="160" text-anchor="middle">${w.measure}</text><text x="255" y="160" text-anchor="middle">${w.replay}</text>`,
 future:w=>`<circle cx="150" cy="91" r="31" class="diag-purple"/><circle cx="62" cy="49" r="23" class="diag-teal"/><circle cx="238" cy="49" r="23" class="diag-teal"/><circle cx="150" cy="160" r="23" class="diag-teal"/><path d="M84 59l39 19 M216 59l-39 19 M150 122v15" class="diag-dash"/><path d="M50 49h24M62 37v24 M228 49h20 M238 39v20 M140 160h20 M150 150v20" class="diag-line"/><text x="62" y="18" text-anchor="middle">${w.binding}</text><text x="238" y="18" text-anchor="middle">${w.repair}</text><text x="197" y="179">${w.physics}</text>`
};
const beforeAtlasIllustrations = showResearch;
showResearch = function(key) {
  beforeAtlasIllustrations(key);
  const copy = atlasCopy[locale];
  const labels = diagramWords[locale];
  const graphic = document.querySelector('#atlas-graphic');
  graphic.innerHTML = `<svg viewBox="0 0 300 200" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">${diagramSVG[key](labels)}</svg>`;
  graphic.setAttribute('aria-label', `${researchNodes[key].title}: ${copy.diagram}`);
  document.querySelector('#atlas-image-caption').textContent = copy.caption;
  document.querySelector('[data-t="atlasCompareHeading"]').textContent = copy.heading;
  document.querySelector('#atlas-other-label').textContent = key === 'future' ? extra[locale].nodeFutureTitle : researchNodes[key].title;
  document.querySelector('#atlas-other-text').textContent = copy[key][0];
  document.querySelector('#atlas-hard-text').textContent = copy[key][1];
};
const beforeAtlasIllustrationsLocale = setLocale;
setLocale = function(lang) { beforeAtlasIllustrationsLocale(lang); showResearch(activeResearch); };
setLocale(locale);
