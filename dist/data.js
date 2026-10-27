// Replace this repository with HTTP-backed methods when a backend is connected.
export const companies = [
 {id:'005930',name:'삼성전자',initial:'S',sector:'반도체',market:'KOSPI',price:'72,400',change:'+1.26%',tone:'blue',points:[48,45,50,46,60,55,65,61,72,70,82,77,90]},
 {id:'000660',name:'SK하이닉스',initial:'SK',sector:'반도체',market:'KOSPI',price:'183,500',change:'+2.18%',tone:'red',points:[40,42,37,50,45,59,54,67,63,80,75,88,92]},
 {id:'035420',name:'NAVER',initial:'N',sector:'인터넷 서비스',market:'KOSPI',price:'178,200',change:'−0.84%',tone:'green',points:[80,83,72,76,68,74,62,65,58,63,51,56,48]},
 {id:'005380',name:'현대자동차',initial:'H',sector:'자동차',market:'KOSPI',price:'241,000',change:'+0.63%',tone:'navy',points:[40,49,45,56,52,63,60,65,61,73,68,80,83]}
];
export const lessons=[{n:'01',category:'시장 기초',title:'주식 한 주를 산다는 것',text:'주주가 된다는 의미부터 시장의 구조까지',time:'5분',tag:'입문',icon:'◉'}, {n:'02',category:'재무제표',title:'숫자 속 기업 이야기 읽기',text:'매출, 영업이익, 현금흐름을 연결해 보세요',time:'8분',tag:'기초',icon:'▥'}, {n:'03',category:'기업가치',title:'좋은 기업과 좋은 가격',text:'PER과 PBR로 가격을 바라보는 새로운 시각',time:'7분',tag:'기초',icon:'◇'}, {n:'04',category:'위험 관리',title:'수익보다 먼저 살펴볼 것',text:'분산투자와 위험 신호를 이해해 보세요',time:'6분',tag:'기초',icon:'⌁'}];
export const terms=[{term:'PER',ko:'주가수익비율',text:'주가가 주당순이익의 몇 배인지 보여주는 지표입니다. 이익이 같다면 주가가 높아질수록 PER도 높아집니다.',formula:'주가 ÷ 주당순이익(EPS)'},{term:'PBR',ko:'주가순자산비율',text:'주가를 주당순자산으로 나눈 값입니다. 기업의 자산과 시장의 평가를 비교할 때 사용합니다.',formula:'주가 ÷ 주당순자산(BPS)'},{term:'거래량',ko:'거래된 주식의 수',text:'일정 기간 사고팔린 주식의 수량입니다. 가격 변화와 함께 살펴보되, 거래량 증가만으로 상승을 단정할 수는 없습니다.'},{term:'부채비율',ko:'자본 대비 부채의 비율',text:'자기자본과 비교해 부채가 얼마나 되는지 보여줍니다. 업종과 현금흐름을 함께 살펴야 합니다.',formula:'부채 ÷ 자기자본 × 100'},{term:'영업이익',ko:'본업에서 벌어들인 이익',text:'매출에서 매출원가와 판매관리비를 뺀 이익입니다. 실제 현금 유입과는 다를 수 있습니다.'}];
export const repository={mode:'demo',async listCompanies(){return companies},async getCompany(id){return companies.find(c=>c.id===id)},async listLessons(){return lessons}};
