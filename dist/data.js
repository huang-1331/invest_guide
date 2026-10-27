// B01 educational demo data. All prices, changes and chart shapes are fictional.
export const companies = [
 {id:'005930',name:'삼성전자',initial:'S',sector:'반도체',market:'KOSPI',price:'72,400',change:'+1.26%',tone:'blue',points:[48,45,50,46,60,55,65,61,72,70,82,77,90]},
 {id:'000660',name:'SK하이닉스',initial:'SK',sector:'반도체',market:'KOSPI',price:'183,500',change:'+2.18%',tone:'red',points:[40,42,37,50,45,59,54,67,63,80,75,88,92]},
 {id:'035420',name:'NAVER',initial:'N',sector:'인터넷 서비스',market:'KOSPI',price:'178,200',change:'−0.84%',tone:'green',points:[80,83,72,76,68,74,62,65,58,63,51,56,48]},
 {id:'005380',name:'현대자동차',initial:'H',sector:'자동차',market:'KOSPI',price:'241,000',change:'+0.63%',tone:'navy',points:[40,49,45,56,52,63,60,65,61,73,68,80,83]}
];
export const lessons = [
  {
    "n": "01",
    "category": "시장 기초",
    "title": "주식 한 주를 산다는 것",
    "text": "주주가 된다는 의미부터 시장의 구조까지",
    "time": "5분",
    "tag": "입문",
    "icon": "◉",
    "content": "주식은 기업 소유권의 일부를 나타냅니다. 한 주를 보유하면 주주가 되지만, 경영권 행사 범위는 보유 주식과 제도에 따라 달라집니다. 주식의 시장가격은 매수자와 매도자의 거래에 따라 달라집니다. 배당은 기업의 결정에 따라 지급될 수 있으며 원금·수익·배당은 보장되지 않습니다.",
    "keyPoints": [
      "주식은 기업 소유권의 일부입니다.",
      "주가는 거래에 따라 변합니다.",
      "주식 투자에는 손실 가능성이 있습니다."
    ],
    "quizId": "Q01"
  },
  {
    "n": "02",
    "category": "재무제표",
    "title": "숫자 속 기업 이야기 읽기",
    "text": "매출, 영업이익, 현금흐름을 연결해 보세요",
    "time": "8분",
    "tag": "기초",
    "icon": "▥",
    "content": "매출액은 일정 기간 상품이나 서비스를 판매해 인식한 수익입니다. 영업이익은 매출액에서 매출원가와 판매비·관리비 등을 반영한 본업 관련 이익입니다. 당기순이익에는 영업 외 항목과 법인세 등도 영향을 줍니다. 손익계산서에 이익이 나더라도 매출채권 증가 등으로 영업현금흐름은 부족할 수 있습니다. 따라서 이익과 현금흐름을 함께 확인합니다.",
    "keyPoints": [
      "매출액과 이익은 다른 개념입니다.",
      "회계상 이익과 현금흐름은 같지 않을 수 있습니다.",
      "비교할 때 기간과 연결·별도 기준을 맞춥니다."
    ],
    "quizId": "Q02"
  },
  {
    "n": "03",
    "category": "기업가치",
    "title": "좋은 기업과 좋은 가격",
    "text": "PER과 PBR로 가격을 바라보는 새로운 시각",
    "time": "7분",
    "tag": "기초",
    "icon": "◇",
    "content": "PER은 주가를 주당순이익(EPS)으로 나눈 값입니다. 예를 들어 주가가 10,000원이고 EPS가 1,000원이면 PER은 10배입니다. EPS가 0 이하일 때는 통상 의미 있는 양(+)의 PER 비교가 어려워 평가 불가로 표시합니다. PBR은 주가를 주당순자산(BPS)으로 나눈 값입니다. PER이나 PBR이 낮다는 이유만으로 주식이 저평가되었다고 단정할 수 없고, 이익의 지속성·부채·성장성·업종을 함께 살펴야 합니다.",
    "keyPoints": [
      "PER = 주가 ÷ EPS입니다.",
      "EPS가 0 이하이면 PER 비교에 주의합니다.",
      "단일 지표로 투자 적합성을 확정하지 않습니다."
    ],
    "quizId": "Q03"
  },
  {
    "n": "04",
    "category": "위험 관리",
    "title": "수익보다 먼저 살펴볼 것",
    "text": "분산투자와 위험 신호를 이해해 보세요",
    "time": "6분",
    "tag": "기초",
    "icon": "⌁",
    "content": "주식 가격은 기업 실적·경제 여건·시장 심리 등 다양한 요인으로 변동합니다. 여러 기업이나 자산에 나누어 투자하면 특정 기업에 집중된 위험을 줄이는 데 도움이 될 수 있지만 시장 전체가 하락하는 위험은 제거하지 못합니다. 기업의 재무정보가 없을 때는 위험이 낮다고 판단하지 말고 평가 불가로 표시해야 합니다. 투자자는 손실 가능성과 자신의 투자기간을 함께 고려해야 합니다.",
    "keyPoints": [
      "분산투자는 손실 가능성을 없애지 않습니다.",
      "실제 자료가 없으면 위험은 평가 불가입니다.",
      "예시 차트는 미래 수익률을 예측하지 않습니다."
    ],
    "quizId": "Q04"
  }
];
export const terms = [
  {
    "term": "PER",
    "ko": "주가수익비율",
    "text": "주가가 주당순이익(EPS)의 몇 배인지 나타냅니다. EPS가 0 이하이면 일반적인 PER 비교가 어렵습니다.",
    "formula": "주가 ÷ EPS",
    "example": "주가 10,000원 ÷ EPS 1,000원 = 10배"
  },
  {
    "term": "PBR",
    "ko": "주가순자산비율",
    "text": "주가를 주당순자산(BPS)으로 나눈 지표입니다. BPS가 0 이하이면 해석에 주의해야 합니다.",
    "formula": "주가 ÷ BPS",
    "example": "주가 10,000원 ÷ BPS 5,000원 = 2배"
  },
  {
    "term": "거래량",
    "ko": "거래된 주식 수",
    "text": "일정 기간 실제로 거래된 주식 수량입니다. 거래량 증가만으로 가격 상승을 단정할 수 없습니다.",
    "example": "하루에 주식 2,000주가 거래되면 일일 거래량은 2,000주입니다."
  },
  {
    "term": "부채비율",
    "ko": "자본 대비 부채 비율",
    "text": "자기자본 대비 부채 규모를 나타냅니다. 업종별 차이를 고려해야 합니다.",
    "formula": "부채총계 ÷ 자본총계 × 100",
    "example": "부채 200억 원 ÷ 자본 100억 원 × 100 = 200%"
  },
  {
    "term": "영업이익",
    "ko": "본업에서 발생한 이익",
    "text": "매출액에서 매출원가와 판매비·관리비 등을 반영한 영업활동의 성과입니다. 현금흐름과는 다릅니다.",
    "example": "매출 100억 원, 영업 관련 원가·비용 85억 원이면 영업이익은 15억 원입니다."
  },
  {
    "term": "주식",
    "ko": "기업 소유권의 일부",
    "text": "기업이 발행한 지분 증권입니다. 주식을 보유한 사람은 주주가 됩니다.",
    "example": "어떤 기업의 주식 1주를 사면 그 기업의 주주가 됩니다."
  },
  {
    "term": "주가",
    "ko": "주식 한 주의 가격",
    "text": "시장에서 거래되는 주식 한 주의 가격으로 거래 시점에 따라 달라질 수 있습니다.",
    "example": "주가 20,000원인 주식 3주의 매수 금액은 수수료 등을 제외하면 60,000원입니다."
  },
  {
    "term": "시가총액",
    "ko": "상장주식 가치의 합계",
    "text": "주가에 상장주식 수를 곱한 값입니다. 기업의 모든 가치를 확정하는 지표는 아닙니다.",
    "formula": "주가 × 상장주식 수",
    "example": "주가 10,000원 × 상장주식 100만 주 = 100억 원"
  },
  {
    "term": "EPS",
    "ko": "주당순이익",
    "text": "보통주 1주에 귀속되는 이익을 나타내는 지표입니다. 실제 EPS는 가중평균 주식 수 등 회계 기준에 따라 계산됩니다.",
    "formula": "보통주 귀속 순이익 ÷ 가중평균 유통보통주식 수(기본 EPS의 개념)",
    "example": "보통주 귀속 순이익 10억 원 ÷ 평균 주식 100만 주 = 1,000원"
  },
  {
    "term": "ROE",
    "ko": "자기자본이익률",
    "text": "주주자본 대비 이익 창출 정도를 나타냅니다. 높은 수치만으로 안전한 기업임을 뜻하지 않습니다.",
    "formula": "당기순이익 ÷ 평균 자기자본 × 100 (간략식)",
    "example": "순이익 10억 원 ÷ 평균 자기자본 100억 원 × 100 = 10%"
  }
];
export const quizzes = [
  {
    "id": "Q01",
    "lessonId": "01",
    "question": "주식을 보유한다는 의미로 올바른 것은?",
    "options": [
      "기업의 소유권 일부를 보유한다.",
      "원금이 반드시 보장된다.",
      "매년 배당이 의무 지급된다.",
      "매수가격에 재판매가 보장된다."
    ],
    "correctIndex": 0,
    "explanation": "주식은 기업 소유권의 일부이며 원금이나 배당이 보장되지 않습니다."
  },
  {
    "id": "Q02",
    "lessonId": "02",
    "question": "영업이익과 현금흐름에 대한 설명으로 맞는 것은?",
    "options": [
      "두 수치는 언제나 같다.",
      "이익이 발생해도 현금흐름은 부족할 수 있다.",
      "매출액은 항상 순이익과 같다.",
      "현금흐름은 재무제표에서 확인할 수 없다."
    ],
    "correctIndex": 1,
    "explanation": "매출채권·재고 등의 변동으로 회계상 이익과 현금 유입은 달라질 수 있습니다."
  },
  {
    "id": "Q03",
    "lessonId": "03",
    "question": "주가 10,000원, EPS 1,000원일 때 PER은?",
    "options": [
      "1배",
      "5배",
      "10배",
      "100배"
    ],
    "correctIndex": 2,
    "explanation": "PER = 주가 ÷ EPS = 10,000 ÷ 1,000 = 10배입니다."
  },
  {
    "id": "Q04",
    "lessonId": "04",
    "question": "분산투자의 효과를 가장 정확히 설명한 것은?",
    "options": [
      "모든 손실을 방지한다.",
      "기업의 실적을 보장한다.",
      "미연결 기업의 위험을 안전으로 판정한다.",
      "특정 기업에 집중된 위험을 줄이는 데 도움을 줄 수 있다."
    ],
    "correctIndex": 3,
    "explanation": "분산투자는 특정 위험을 줄일 수 있지만 시장 전체의 손실 위험을 없애지 못합니다."
  }
];
export const perPractice = { id:'PER01', price:10000, eps:1000, expectedPer:10, currency:'KRW', isSample:true, note:'가상 실습값이며 실제 종목 재무정보가 아닙니다.' };
export function calculatePer(price, eps) {
  if (!Number.isFinite(price) || !Number.isFinite(eps) || price < 0 || eps <= 0) return null;
  return price / eps;
}
export const dataMeta = {mode:'demo',priceType:'illustrative',source:'교육용 임의 생성 데이터',asOf:null,disclaimer:'기업명과 종목코드는 실제 식별정보이나 가격·등락률·차트는 가상의 예시이며 실제 시세가 아닙니다.'};
export const repository={
  mode:'demo',
  async listCompanies(){return companies},
  async getCompany(id){return companies.find(c=>c.id===id) ?? null},
  async listLessons(){return lessons},
  async getLesson(n){return lessons.find(l=>l.n===n) ?? null},
  async listTerms(){return terms},
  async listQuizzes(){return quizzes},
  async getQuizForLesson(n){return quizzes.find(q=>q.lessonId===n) ?? null}
};