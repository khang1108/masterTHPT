# 1. Tổng quan dự án
## 1.1 Tên dự án
MASTER - Multi-Agent System for Teaching, Evaluating & Reviewing
## 1.2 Mô tả ngắn gọn
MASTER (Multi-Agent System for Teaching, Evaluating & Reviewing) là một nền tảng EdTech tiên tiến được vận hành hoàn toàn bởi Multi-Agent System (MAS), được thiết kế chuyên biệt để hỗ trợ học sinh THPT tối ưu hóa quá trình ôn luyện, học tập cho các kỳ thi (Giữa kỳ, Cuối kỳ, THPTQG, V-ACT, HSA, …). 

Khác với các ứng dụng học tập hiện có trên thị trường (SHub, K12, VietJack, …) chỉ cung cấp một trang web hoặc ứng dụng một chiều và dữ liệu tĩnh, thì MASTER cung cấp một môi trường giả lập phòng thi toàn diện, giúp cho học sinh quen với áp lực thực tế. Bên cạnh đó, hệ thống còn là nơi tổng hợp các đề thi khác nhau (Tỉnh, trường, sở, thành phố, …) theo các môn, giúp học sinh tiết kiệm thời gian tìm kiếm trên Internet cũng như có thể cá nhân hóa lộ trình học tập dựa trên dữ liệu thực.
## 1.3 Vấn đề và giải pháp
### 1.3.1 Đặt vấn đề
Trong bối cảnh giáo dục THPT hiện nay, học sinh phải đối mặt với áp lực lớn từ các kỳ thi định kỳ, THPT Quốc gia, Đánh giá năng lực, HSA, TSA… Để đạt kết quả cao, học sinh không chỉ nỗ lực mà còn phải có một chiến lược ôn luyện hiệu quả, phù hợp với năng lực cá nhân. Tuy nhiên, hiện nay các nền tảng giáo dục vẫn chưa đáp ứng trọn vẹn được nhu cầu này.
MASTER được phát triển để giải quyết ba nút thắt chính của học sinh trong việc học tập và ôn luyện cho các kỳ thi lớn:
Chi phí tìm kiếm lớn: Các học sinh phải dành hàng giờ đồng hồ trên các nền tảng mạng xã hội, Internet để có thể tìm kiếm các bài tập, các bài kiểm tra khác nhau, nhưng lại không có lời giải hoặc là không phù hợp với bản thân (quá khó, quá dễ, …).
Thiếu hụt sự cá nhân hóa: Các bài tập hoặc các bài kiểm tra trên mạng thường được thiết kế với độ khó tăng dần và phù hợp với đại đa số học sinh (tuân theo phân phối chuẩn). Việc này khiến cho quá trình ôn tập và học tập của học sinh trở nên khó khăn hơn. Như nhiều trang web ôn thi THPT trực tuyến cung cấp đề thi và bài tập (toanmath.com, thithu.edu.vn, …), phần lớn nội dung chỉ là ngân hàng có sẵn; hệ thống không điều chỉnh theo năng lực cá nhân của từng học sinh.
Hạn chế về trải nghiệm: Các nền tảng học tập trên thị trường thường được thiết kế theo mô hình giáo viên quản lý lớp học, tương tác một chiều và không còn tính năng nào khác. Điều này làm cho học sinh thiếu đi môi trường luyện tập và rèn luyện bản thân. Theo báo Quân đội Nhân dân, nhiều phần mềm học trực tuyến như K12 Online, SHub Classroom... phản ánh rằng mỗi công cụ chỉ đáp ứng một phần nhu cầu, và khi sử dụng thực tế, giáo viên và học sinh loay hoay mãi mới tổ chức được lớp học ảo, còn lại các tính năng khác như tương tác sâu, luyện tập đa dạng hay môi trường đào tạo toàn diện lại chưa thực sự hiệu quả.
Thiếu môi trường cọ xát thực tế (Áp lực phòng thi): Các kỳ thi quan trọng không chỉ đòi hỏi kiến thức mà còn thử thách bản lĩnh tâm lý và kỹ năng phân bổ thời gian. Đa số ứng dụng hiện nay chỉ dừng ở mức cho học sinh "giải bài tập" ở trạng thái tự do. Việc thiếu vắng một không gian giả lập phòng thi toàn diện với đồng hồ đếm ngược, quy chế làm bài nghiêm ngặt và mức độ tập trung cao độ khiến học sinh dễ bị "khớp" tâm lý, dẫn đến kết quả thực tế không phản ánh đúng năng lực khi bước vào kỳ thi chính thức.
### 1.3.2 Câu hỏi đặt ra
Mặc dù hệ thống giáo dục Việt Nam đã gặt hái được nhiều thành tựu đáng tự hào, quá trình chuyển đổi số hiện nay đang đặt ra những yêu cầu khắt khe hơn về công nghệ sư phạm. Bài toán cốt lõi không còn dừng lại ở việc "đưa công nghệ vào lớp học" hay sử dụng AI như một công cụ vấn đáp đơn thuần. Thay vào đó, giáo dục hiện đại đòi hỏi một giải pháp vận hành tổng thể: một hệ thống có khả năng tự động xử lý các nhiệm vụ học tập phức tạp, biết phối hợp đa vai trò để đồng hành cùng người học. Nhu cầu này hoàn toàn đồng điệu với định hướng mới của Bộ Giáo dục và Đào tạo trong việc thí điểm khung năng lực AI tại bậc phổ thông, nơi tính ứng dụng phải đi đôi chặt chẽ với sự minh bạch, đạo đức và khả năng kiểm soát công nghệ.
Để có thể thực hóa được dự án và chứng minh được tính khả thi của toàn dự án thì nhóm đã đặt ra các câu hỏi câu hỏi cốt lõi như sau:
Nguồn dữ liệu sẽ được lấy từ đâu?: Để trả lời câu hỏi này, nhóm đã tìm hiểu các nền tảng học thuật và cung cấp các tài liệu, đề thi các môn khác nhau trên mạng Internet như toanmath.com, thcs.toanmath.com, vietjack.com, ….
Hệ thống sẽ hỗ trợ cho học sinh trong khía cạnh và use case nào?: Hệ thống đóng vai trò như là một người gia sư 24/7 sẽ cung cấp cho người dùng các câu hỏi, bài tập và mô phỏng kiểm tra thực tế giúp cho học sinh có thể luyện tập và làm quen với áp lực. Học sinh có thể tải lên là một bức ảnh, là một file pdf, hoặc một file docx thì hệ thống sẽ tự suy luận và lên kế hoạch để có thể đạt được mục tiêu cuối cùng của user.
Chi phí hạ tầng và chi phí để vận hành các AI liệu có phù hợp với nhóm?: Với sự hỗ trợ từ ban tổ chức, nhóm hoàn toàn có thể vận hành một Self-Hosting GPU Server, triển khai các open-source AI model để có thể hoàn thành ý tưởng của dự án.
Hệ thống sẽ phải cung cấp các tính năng gì để có thể khác biệt so với các sản phẩm có trên thị trường?: Để trả lời được câu hỏi này, nhóm đã phải đi khảo sát rất nhiều các nền tảng E-Learning khác nhau hiện có trên thị trường như SHub, K12, Moodle, … qua đó có thể đưa ra một góc nhìn tổng quan về điểm mạnh, điểm yếu của sản phẩm, và qua đó nhóm đã quyết định xây dựng các tính năng như: mô phỏng kiểm, ôn luyện theo điểm yếu, luyện tập giải đề. Và nhóm tin rằng các tính năng này chưa hoặc rất ít được phát triển trong các sản phẩm.
Hệ thống sẽ đánh giá học sinh theo tiêu chuẩn nào? Hiện nay có rất nhiều tiêu chuẩn đánh giá học sinh như cognitive-dimension, behavioral dimension, IRT, … Để lựa chọn được tiêu chí đánh giá, nhóm sẽ cần phải khảo sát thêm, xác định được mục đích của các bài kiểm tra mà nhóm hướng đến (e.g. Đánh giá năng lực, V-ACT, …)
Với mỗi stage của hệ thống, làm sao để đánh giá độ hiệu quả của các mô hình?Đối với mỗi Agent thì sẽ có một tiêu chí đánh giá riêng, nên việc lựa chọn tiêu chí đánh giá ảnh hưởng rất lớn tới độ chính xác của hệ thống. Chẳng hạn, Parser sẽ dùng CER để đánh giá extracting, hoặc Teacher sẽ có MAE để đó được chênh lệch điểm đánh giá với con người.
### 1.3.3 Giải pháp đề xuất
Để giải quyết triệt để những thách thức đã đặt ra, hệ thống Multi-Agent System mang tên MASTER được đề xuất nhằm tháo gỡ ba nút thắt lớn của học sinh Việt Nam hiện nay: thiếu tính cá nhân hóa, thiếu công cụ đánh giá học tập chuyên sâu và hạn chế về một môi trường rèn luyện thông minh. 
Trong bối cảnh các lớp học thường quá tải khiến giáo viên khó theo sát từng cá nhân, cùng với mức độ sẵn sàng ứng dụng AI chưa đồng đều, MASTER bứt phá khỏi giới hạn của một chatbot vấn đáp đơn lẻ bằng cách tổ chức một hệ sinh thái AI cộng tác. Tại đây, các tác tử chuyên biệt phân vai nhịp nhàng để hiện thực hóa chu trình khép kín: theo dõi – đánh giá – giải thích – điều chỉnh. Hệ thống tận dụng công nghệ truy xuất thông tin tiên tiến để rút ngắn thời gian tìm kiếm học liệu xuống mức tối thiểu, đồng thời duy trì ngữ cảnh xuyên suốt để vạch ra lộ trình khắc phục chính xác từng lỗ hổng tư duy của người học.
Điểm tạo nên giá trị cốt lõi của MASTER là môi trường luyện tập đa chiều, nơi bài làm của học sinh không chỉ được phân tích mà còn trải qua quá trình phản biện, kiểm tra chéo nghiêm ngặt giữa các agent. Cơ chế này không những mô phỏng được áp lực rèn luyện thực chiến mà còn triệt tiêu rủi ro sai sót của các mô hình ngôn ngữ lớn, biến quá trình chấm chữa trở nên minh bạch và đáng tin cậy. Nói cách khác, MASTER vận hành như một đội ngũ gia sư AI tận tụy, mang đến cho nhà trường và học sinh một mô hình học tập cá nhân hóa sâu sắc, liên tục và hoàn toàn đáp ứng tiêu chuẩn an toàn công nghệ của giáo dục hiện đại.
# 2. Kiến trúc hệ thống Agent
Hệ thống được xây dựng theo mô hình Director-Employees, trong đó, Manager Agent làm nhiệm vụ điều phối trung tâm, lập kế hoạch và ủy quyền xử lý xuống các tác tử chuyên biệt (Parser, Teacher, Verifier) thông qua giao thức message-passing (JSON chuẩn hóa), đảm bảo khả năng mở rộng và truy vết toàn diện."
## 2.1 Manager Agent
Manager Agent có vai trò tiếp nhận mọi yêu cầu của người dùng, phân tích ngữ cảnh, lập kế hoạch thực thi theo cấu trúc DAG và phân công công việc cho các agents cấp dưới để hoàn thiện công việc mong muốn từ người dùng hoặc là của chính agent. 
Đầu vào của Manager Agent sẽ là một prompt hoàn chỉnh áp dụng kỹ thuật Chain of Thought (CoT) để đưa ra các suy luận từng bước hợp lý, logic và đầy đủ nhất. Prompt có cấu trúc như sau:

```bash
Input: "Tôi muốn làm đề thi thử Toán THPTQG 2025"
                    ↓
Step 1 -- Intent Detection:
  - Keywords: "đề thi thử", "Toán", "THPTQG", "2025"
  - Classified intent: EXAM_PRACTICE
  - Sub-intent: FULL_EXAM (not topic-specific)
                    ↓
Step 2 -- Context Enrichment:
  - Query UserDB → student_id: S001
  - Current mastery: {algebra: 0.72, geometry: 0.45, calculus: 0.88}
  - Last exam score: 7.2/10
  - Weak topics: ["geometry", "trigonometry"]
                    ↓
Step 3 -- Task Graph Construction (DAG):
  T1: Adaptive Agent → select exam matching student level
  T2: Teacher Agent → prepare exam session (timer, rules)
  T3: [After student submits] Parser Agent → extract answers
  T4: Teacher Agent → grade with rubric
  T5: Verifier Agent → cross-check grading
  T6: Adaptive Agent → update student profile
                    ↓
Step 4 -- Dispatch:
  Execute T1 → T2 sequentially
  Wait for student submission
  Execute T3 → T4 → T5 → T6 sequentially

Prompt 1: Prompt chi tiết cung cấp cho Manager Agent  

User Intent
Agent Flow
Constraint
EXAM_PRACTICE
Adaptive → Teacher → (submit) → Parser → Teacher → Verifier → Adaptive
Học sinh muốn làm bài thi (mới vào ứng dụng)
GRADE_SUBMISSION
Parser → Teacher → Verifier
Học sinh nộp bài bằng ảnh (PDF/ jpg/ png)
VIEW_ANALYSIS
Adaptive → Manager (Render)
Phân tích năng lực học sinh
ASK_HINT
Teacher -> RAG
Hiện gợi ý
REVIEW_MISTAKE
USER_DATABASE → Teacher
Xem lại nhận xét
UNKNOWN
Manager → Clarification loop
Không xác định được intent
```
Bảng 1: Bảng các luồng hoạt động của Manager

| Tool| Mô tả | Context |
| --- | --- | --- |
query_user_db| Truy vấn lịch sử học của người dùng trên Database| Khi cần dữ liệu từ lịch sử người dùng
fetch_exam_metadata| Lấy metadata của đề thi, bài tập (src, năm, môn, topic)| Khi cần lấy đề thi
read_session_state| Lấy trạng thái hiện tại của user | Xác định xem người dùng đang thi, hay practice, …
search_exam_bank| Tìm kiếm câu hỏi trong kho đề| Khi đang ở EXAM_PRACTICE
ground_browser| Tìm kiếm các trang web, ghé thăm và lấy các tài liệu|Khi cần làm giàu EXAM_BANK

Bảng 2: Các công cụ được cung cấp cho Manager


Output: Dữ liệu được chuẩn hóa dưới dạng JSON payload, bao gồm hai luồng chính:
- Luồng điều phối (Internal): Phân phát các gói lệnh (Instruction) kèm theo ngữ cảnh đã chắt lọc (Context Window) xuống các agent cấp dưới để tối ưu token và tránh nhiễu thông tin.
- Luồng tổng hợp (External): Đóng gói kết quả cuối cùng (sau khi Teacher và Verifier đã đồng thuận) để cập nhật vào UserDB và trả về giao diện cho học sinh.

## 2.2. Parser Agent
Parser Agent có nhiệm vụ xử lý các ảnh được cung cấp bởi user, tiền xử lý ảnh, giảm nhiễu, giảm sáng, bóc tách, nhận diện chữ viết tay, trích xuất thành một file JSON có cấu trúc.
Đầu vào của ParserAgent sẽ là các yêu cầu được truyền xuống từ ManagerAgent thông qua cấu trúc JSON và các tệp PDF/PNG/JPEG/JPG. Agent này sẽ hoạt động cũng theo cơ chế Chain of Thought (CoT) để có thể đưa ra các suy luận, các luồng suy nghĩ trong việc sử dụng các tools được cung cấp cho xử lý ảnh và trích xuất câu hỏi. Cốt lõi của Agent này chính là khả năng xử lý thông qua thư viện OpenCV được đóng gói bên trong các hàm như reduce_noise(), convert_to_gray(), … sau đó sẽ được truyền vào bộ não PaddleOCR và PP-OCRv5 để có thể xác định được vị trí các câu hỏi, cắt ảnh và trích xuất nội dung sang cấu trúc JSON thuận tiện cho việc lưu trữ.
Hình 1: Workflow của Parser

| Stage| Technology | Brief|
| --- | --- | --- |
| Image Preprocessing| OpenCV, NumPy| Cung cấp các công cụ hỗ trợ Agent cho việc tiền xử lý ảnh|
| Text Detection| PaddleOCR PP-OCRv5| Nhận diện những vùng là câu hỏi |
| Formula Recognition| PP-FormulaNet+| Nhận diện các công thức và chuyển nó thành Latex|
| Visual Understanding| Gemini 2.5 Flash| Phân tích các hình vẽ, các đồ thị |
| Layout Parsing| VLM | Xác định và hiểu đươc cấu trúc của đề, hiểu được header, và thứ tự sắp xếp các phần tử bên trong|
| Question Extraction| LLM Structured Output | Tách từng câu hỏi được nhận diện và chuyển thành JSON|

Bảng 3: Các kỹ thuật bên trong Parser
```json
{
  "exam_id": "auto-generated",
  "source": "image | pdf",
  "subject": "math",
  "exam_type": "THPTQG_2025",
  "total_questions": 50,
  "sections": [
    {
      "type": "multiple_choice",
      "questions": [
        {
          "id": "q1",
          "content": "Tìm nguyên hàm của f(x) = 2x + 1",
          "content_latex": "\\text{Tìm nguyên hàm của } f(x) = 2x + 1",
          "options": ["A. x² + x + C", "B. x² + C", "C. 2x² + x + C", "D. x + C"],
          "has_image": false,
          "difficulty_estimate": 0.3,
          "topic_tags": ["calculus", "antiderivative"]
        }
      ]
    },
    {
      "type": "essay",
      "questions": [
        {
          "id": "q41",
          "content": "Cho hình chóp S.ABCD có đáy là hình vuông...",
          "has_image": true,
          "image_description": "Hình chóp tứ giác đều với SA vuông góc mp(ABCD)",
          "sub_parts": ["a", "b", "c"],
          "max_score": 1.0
        }
      ]
    }
  ],
  "student_answers": {
    "q1": "A",
    "q41": { "raw_text": "...", "latex": "..." }
  }
}
```
Prompt 2: Cấu trúc file JSON cho một câu hỏi được trích xuất

## 2.3. Teacher Agent
Teacher Agent là một agent đảm nhiệm vai trò chấm bài, phân tích lỗi tư duy, chỉ ra lỗi sai và đưa ra các lời phản hồi cho người dùng, những lời nhận xét, chỉ ra các điểm yếu cần sửa lỗi. 
Hình 3: Workflow của Teacher

Đầu vào của Teacher là các lệnh được truyền từ Manager xuống và bài làm của học sinh, sau đó Teacher Agent sẽ tiến hành truy vấn các Rubric sẵn có trong Database để chấm bài (THPTQG, V-ACT, HSA, …). Nếu như không có Rubric phù hợp cho bài làm của học sinh, thì Agent sẽ tiến hành đi tìm kiếm trên Internet Rubric phù hợp và lưu nó vào database. Sau đó, Teacher phải truy vấn các cuốn sách giáo khoa phù hợp với kiến thức của bài kiểm tra mà học sinh làm (Toán 12, Toán 11, Văn 10, …). Hệ thống tiến hành xác minh bài làm theo từng loại câu hỏi của học sinh (chi tiết tại Bảng 3), sau đó đưa ra lời giải thích tương ứng. Tiếp theo đó, hệ thống tiến hành phân tích các lỗi sai, đưa ra các lời đánh giá, các điểm yếu và hiểu lầm trong kiến thức. 

| Loại câu hỏi| Cách chấm| Chi tiết|
| --- | --- | --- |
| Trắc nghiệm| Exact Match| So sánh đáp án, chỉ có đúng hoặc sai hoặc là A/B/C/D. Nếu sai thì cho ra lời giải chi tiết.
| Tự luận ngắn| Semantic Similarity| Embedding bài làm theo từng câu và cho lời giải. Sau đó tính toán similarity >= threshold (khoảng 0.85)
| Tự luận dài| LLM-as-a-judge + RAG| Đánh giá theo Rubric, có tham chiếu đáp án và chấm theo context
| Bài toán tính, lập luận| Viết ra các hàm tính toán bằng Python và execute nó| So khớp với tính toán bằng Python và bài làm

Bảng 3: Cách thức chấm điểm và kỹ thuật tại giai đoạn Answer Verification
Đối với Error Analysis (sẽ bổ sung thêm):
```json
{
  "error_taxonomy": {
    "CONCEPT_GAP": "Hổng kiến thức nền tảng (VD: không biết công thức tích phân)",
    "CALCULATION_ERROR": "Sai số tính toán (VD: 3×4=11)",
    "INCOMPLETE_REASONING": "Thiếu bước trung gian trong lời giải",
    "MISINTERPRETATION": "Hiểu sai đề bài",
    "PRESENTATION_FLAW": "Trình bày không rõ ràng, thiếu ký hiệu"
  }
}

Prompt 3: Ghi nhận lỗi của user
Và cuối cùng Teacher Agent sẽ cho một bản nháp đánh giá của người dùng:
{
  "evaluation_id": "eval-uuid",
  "exam_id": "exam-uuid",
  "student_id": "S001",
  "total_score": 7.25,
  "max_score": 10.0,
  "confidence": 0.82,
  "per_question": [
    {
      "question_id": "q1",
      "student_answer": "A",
      "correct_answer": "A",
      "is_correct": true,
      "score": 0.2,
      "reasoning": "Đáp án đúng. Nguyên hàm F(x) = x² + x + C"
    },
    {
      "question_id": "q41",
      "score": 0.5,
      "max_score": 1.0,
      "reasoning": "Học sinh xác định đúng hình chiếu H nhưng tính sai khoảng cách...",
      "error_analysis": {
        "error_type": "CALCULATION_ERROR",
        "root_cause": "Áp dụng sai định lý Pythagore 3D",
        "knowledge_component": "solid_geometry.distance_point_to_plane",
        "remedial": "Ôn lại: Khoảng cách từ điểm đến mặt phẳng trong hình học không gian"
      }
    }
  ],
  "overall_analysis": {
    "strengths": ["calculus", "algebra"],
    "weaknesses": ["solid_geometry", "trigonometry"],
    "topic_gap_details": [...]
  }
}

Prompt 4: Draft Evaluation của Teacher
2.4. Verifier Agent
Verifier Agent có nhiệm vụ phản biện lại bản nháp đánh giá của Teacher phía trên, đưa ra các lập luận riêng, các đánh giá riêng về bài làm của học sinh. Từ đó, cả hai cùng nhau thống nhất lại một bản đánh giá cuối cùng. Điểm cốt lõi làm cho cơ chế này đáng tin cậy là: mọi lập luận của cả hai bên đều phải được neo đậu (ground) bằng bằng chứng từ công cụ bên ngoài trước khi được chấp nhận vào vòng tranh luận. Điều này đảm bảo sự phản biện không dừng lại ở mức "LLM đồng ý với LLM" mà phải là "bằng chứng xác minh được đồng thuận với bằng chứng xác minh được".
Algorithm: Teacher-Verifier Adversarial Debate
Input: draft_evaluation (from Teacher), student_work, exam_context
Output: final_evaluation (consensus or escalated)
Parameters: MAX_ROUNDS = 3, AGREEMENT_THRESHOLD = 0.9, MIN_EVIDENCE_CONFIDENCE = 0.6


Round 0: Pre-verification & Independent Assessment 
     // Pre-verification — loại câu có ground truth ra khỏi debate   
  0. FOR each q in exam: 
       ground_truth[q.id] = ground_truth(q)  // None nếu là essay 
       skip_debate = {q.id | ground_truth[q.id] is not None}
  1. verifier_eval = Verifier.grade_independently(student_work, exam_context)
     // Verifier tra cứu đáp án từ nguồn riêng (khác Teacher)
  2. discrepancies = compare(draft_evaluation, verifier_eval, exclude=skip_debate)
     // So sánh từng câu: score, error_type, reasoning
  3. IF len(discrepancies) == 0:
       RETURN build_final(draft_evaluation, ground_truth)  // Đồng thuận ngay
     ELSE:
       flag_items = discrepancies  // Gắn cờ các điểm bất đồng

FOR round = 1 TO MAX_ROUNDS:
  
  Step 1 -- Verifier gửi phản biện:
    FOR each flagged_item in flag_items:
      verifier_evidence = Verifier.fetch_evidence(flagged_item)
      // Bằng chứng thiếu thuyết phục
      IF verifier_evidence.confidence < MIN_EVIDENCE_CONFIDENCE: 
        flag_items[flagged_item].status = "UNRESOLVABLE"; CONTINUE
      counter_argument = Verifier.generate_argument(
        flagged_item,
        verifier_evidence,  // Bằng chứng từ nguồn độc lập
        reason_for_disagreement
      )
    
  Step 2 -- Teacher phản hồi:
    FOR each counter_argument:
      teacher_evidence = Teacher.fetch_evidence(counter_argument)
      IF teacher_evidence.confidence < MIN_EVIDENCE_CONFIDENCE: 
         decision = "PARTIAL_ACCEPT"; CONTINUE  // Không evidence → không thể DEFEND
      teacher_response = Teacher.respond(
        counter_argument,
        teacher_evidence,
        decision: "ACCEPT" | "DEFEND" | "PARTIAL_ACCEPT"
      )
    
  Step 3 -- Tính Agreement Score:
    agreement_score = count(resolved_items) / count(total_flagged_items)
    
  Step 4 -- Kiểm tra điều kiện dừng:
    IF agreement_score >= AGREEMENT_THRESHOLD:
      RETURN merge_evaluations(teacher_eval, verifier_accepted_changes)
    
    // Cập nhật flag_items cho round tiếp theo
    flag_items = remaining_unresolved_items

// Nếu sau MAX_ROUNDS vẫn bất đồng:
FOR each unresolved_item: 
   IF one_side_cites_rubric AND other_side_does_not: 
      ACCEPT side_with_rubric_citation 
   ELSE: score = avg(teacher_score, verifier_score) → human_review_queue 
RETURN build_final(final_evaluation + audit_trail + human_review_queue)
```
Code 1: Cơ chế hoạt động của Verifier
Đầu vào của Verifier sẽ là bản Draft Evaluation được cung cấp bởi Teacher. Sau đó, cả hai sẽ phản biện lại và đưa ra các lập luận riêng. Cả hai đều được cung cấp các công cụ để phục vụ cho việc chấm bài (search engine, query db, …). Cả hai sẽ giao tiếp với nhau thông qua các tin nhắn được viết dưới dạng JSON, trong đó bao gồm discrepancy_detection. 

| Loại| Mô tả| Example|
| --- | --- | --- |
| SCORE_MISMATCH| Điểm số cả hai khác nhau| Teacher chấm câu 1 0.5đ, nhưng câu 2 là 0.75đ|
| ERROR_TYPE_CONFLICT| Phân loại lỗi khác nhau| Teacher CONCEPT_GAP nhưng Verifier là CALCULATION_ERROR|
| REASONING_FLAW| Lỗi logic trong lúc suy luận| Teacher chấm sai, hiểu sai rubric|
| MISSED_PARTIAL_CREDIT| Bỏ sót điểm thành phần trong Rubric| Teacher bỏ qua một ý thành phần nhỏ trong câ|

Bảng 4: Các loại lỗi được định nghĩa khi chấm chéo

## 2.5. Adaptive Agent
Adaptive Agent là một agent có khả năng duy trì và cập nhật mô hình năng lực học sinh tự động, điều chỉnh độ khó của các câu hỏi, các chủ đề cần phải luyện tập và đưa ra các lộ trình học tập phù hợp cho học sinh. Agent này sẽ cố gắng tạo một mô hình riêng cho từng học sinh dựa vào BKT - Bayesian Knowledge Tracing (BKT) và IRT để có thể đánh giá được khả năng học tập và hiệu quả làm việc của học sinh trên mỗi bài tập. 

Ví dụ như:

| Tham số| Ý nghĩa| Giá trị |
| --- | --- | --- |
| P(L0)| Xác suất đã biết Knowledge Component này trước | 0.1 - 0.5, tinh chỉnh dựa theo các test|
| P(T)| Xác suất học được KC sau mỗi lần tập| 0.1|
| P(S)| Xác suất biết mà là làm| 0.05|
| P(G)| Xác suất không biết nhưng đoán trúng| 0.25|


Các thông số chỉ là ví dụ nhỏ trong toàn bộ hệ thống. Các giá trị mặc định sau này sẽ được nhóm thử nghiệm, tính toán lại thông qua các hàm xác suất khác nhau để có thể đưa ra một giá trị tối ưu cho toàn bộ hệ thống.

// Khi học sinh trả lời ĐÚNG:

$$P(Lₙ | correct) = P(Lₙ₋₁) × (1 − P(S)) / [P(Lₙ₋₁) × (1 − P(S)) + (1 − P(Lₙ₋₁)) × P(G)]$$

// Khi học sinh trả lời SAI:

$$P(Lₙ | wrong) = P(Lₙ₋₁) × P(S) / [P(Lₙ₋₁) × P(S) + (1 − P(Lₙ₋₁)) × (1 − P(G))]$$

// Cập nhật mastery (có tính learning transition):

$$P(Lₙ) = P(Lₙ | obs) + (1 − P(Lₙ | obs)) × P(T)$$

Code 2: Update các trọng số thông qua các hàm xác suất

Theo Item Response Theory (IRT) xác suất được tính:

$$P(correct | θ, a, b) = 1 / (1 + exp(−a × (θ − b)))$$

Trong đó: 
- θ: năng lực học sinh
- a: cấp độ của câu hỏi
- b: độ khó câu hỏi

Khi học sinh vừa mới tham gia hệ thống, thì học sinh sẽ phải làm một bài test khoảng 10-20 câu để có thể ước các tham số ban đầu cho IRT. Sau đó, khi đã đủ số lượng câu hỏi và dữ liệu cho việc đánh giá, thì hệ thống tiến chuyển sang BKT cho mỗi KC để có thể tracing chi tiết tiến độ học tập của người dùng. Khi đó trọng số của IRT sẽ giảm dần, còn trọng số của BKT sẽ tăng đần theo lượng data của user. Đây chính là một hybrid strategy.

Hệ thống sẽ sử dụng cơ chế Computerized Adaptive Testing (CAT) để có thể lựa chọn câu hỏi tiếp theo dựa trên năng lực hiện tại của học sinh thay vì đưa ra cùng một bộ câu hỏi cho tất cả mọi người. Nhờ đó mà hệ thống có thể cá nhân hóa quá trình học tập và tối ưu thời gian của học sinh.

Algorithm: Adaptive Question Selection
``` bash
Input: θ_current (current ability estimate), item_bank, answered_items
Output: next_question

1. candidate_pool = item_bank \ answered_items  // Loại câu đã làm

2. FOR each item i in candidate_pool:
     // Fisher Information tại θ hiện tại:
     I_i(θ) = a_i² × P_i(θ) × (1 − P_i(θ))
     
     // Trong đó P_i(θ) = 1 / (1 + exp(−a_i(θ − b_i)))

3. // Chọn câu có information cao nhất (gần ZPD nhất):
   next_question = argmax_i { I_i(θ) }
   
   // Constraint: |θ − b_i| < 1.5 logits (đảm bảo trong ZPD)
   // Constraint: content_balance (không quá nhiều câu cùng topic)
   // Constraint: exposure_control (không lộ câu hỏi hay)
```
Code 4: Thuật toán Maximum Fisher Information

Việc lựa chọn câu hỏi sẽ dựa trên Zone of Proximal Development (ZPD) Mapping: 
Hình 3: Zone of Proximal Development
## 2.6. Knowledge Graph - Cấu trúc các chủ đề từng môn
Nhằm tối ưu hóa quá trình giám sát tiến độ và cá nhân hóa trải nghiệm giáo dục, hệ thống triển khai tích hợp kiến trúc Đồ thị Tri thức (Knowledge Graph). Thành phần này đóng vai trò như một "bản đồ tư duy số hóa", thực hiện việc biểu diễn cấu trúc phân cấp tuần tự của từng môn học, đồng thời ánh xạ đa chiều mối tương quan logic và điều kiện tiên quyết giữa các chương, bài học.

Đặc biệt, khi kết hợp Knowledge Graph với mô hình Dấu vết Kiến thức (Bayesian Knowledge Tracing - BKT được lưu trữ tại PostgreSQL), hệ thống có khả năng nội suy chính xác tọa độ các "lỗ hổng" kiến thức của học sinh. Dựa trên bản đồ mạng lưới này, các tác tử AI có thể tự động truy xuất ngược các khái niệm nền tảng bị hổng, từ đó chủ động khởi tạo lộ trình học tập cá nhân hóa và đề xuất các bài kiểm tra hoặc học liệu khắc phục mục tiêu một cách chuẩn xác.
## 3. Công nghệ dự kiến sử dụng
Để hiện thực hóa tầm nhìn của MASTER trong việc xây dựng hệ sinh thái giáo dục thông minh - từ việc tự động hóa tổng hợp đề thi đến việc thiết lập lộ trình học tập cá nhân hóa - việc lựa chọn công nghệ không chỉ dừng lại ở việc lắp ghép các công cụ. Chiến lược của chúng tôi được định hình bởi ba trụ cột: Năng lực suy luận đa nhiệm, Độ tin cậy & Bảo mật (RAI), và Khả năng mở rộng linh hoạt.

Dưới đây là kiến trúc chi tiết minh họa cách các công nghệ được tích hợp để tạo ra một hệ thống giáo dục an toàn và hiệu quả:
### 3.1 Công nghệ AI
Thay vì phụ thuộc hoàn toàn vào một API trả phí đắt đỏ, MASTER sử dụng chiến lược Multi-Model Routing, kết hợp sức mạnh của các mô hình mã nguồn mở chạy cục bộ (local) và các API siêu nhẹ để tối ưu hóa cả tốc độ lẫn chi phí:

Manager Agent: Sử dụng các LLMs như Qwen3-8B hoặc Gemini 2.5 Flash để đạt tốc độ phản hồi cực nhanh trong việc điều phối luồng và phân tích ý định người dùng. 

Teacher Agent: Sử dụng Gemma 3 4B – một mô hình nhỏ gọn nhưng xuất sắc trong các tác vụ logic và phản biện chéo, lý tưởng để kiểm soát "hallucination".

Verifier Agent: Triển khai Qwen3-14B Quantized. Việc lượng tử hóa (quantization) giúp mô hình có khả năng suy luận sư phạm sâu sắc, xử lý logic phức tạp mà vẫn chạy mượt mà trên giới hạn phần cứng. 

Vision & OCR (Parser Agent): Tích hợp các công cụ chuyên biệt như PaddleOCR, PP-OCRv5, PP-FormulaNet+ hoặc DeepseekOCR để bóc tách chính xác ký tự và công thức toán học từ ảnh chụp, kết hợp VLM để hiểu bố cục (layout) đề thi.

### 3.2 Hạ tầng
Hạ tầng của MASTER được thiết kế theo tiêu chuẩn của các ứng dụng web quy mô lớn, đặt sự an toàn dữ liệu của người dùng lên hàng đầu.

Google Cloud Provider (GCP): Dự án được triển khai toàn diện trên Google Cloud Platform. Sự đồng bộ trong hệ sinh thái GCP cho phép chúng tôi tận dụng tối đa sức mạnh của Vertex AI, đồng thời thiết lập các chốt chặn giám sát (monitoring) và lưu vết (logging) minh bạch—đáp ứng nghiêm ngặt các tiêu chuẩn của AI có trách nhiệm.  

Self-hosted GPU Server: Các tác vụ suy luận nặng và chuyên biệt (Qwen3-14B, Gemma 3 4B, PaddleOCR/DeepseekOCR) được đóng gói và triển khai trên cụm máy chủ GPU H100 trên nền tảng FPT AI Cloud. Việc đẩy các luồng xử lý ngốn tài nguyên (chấm bài, phản biện) về server local giúp đảm bảo quyền riêng tư tuyệt đối cho dữ liệu học sinh.

Kiến trúc Đa Cơ sở dữ liệu (Multi-Database Strategy):

Google Cloud Storage: Lưu trữ học liệu, file PDF và ảnh chụp đề thi với cơ chế mã hóa đầu cuối (end-to-end encryption), bảo vệ tuyệt đối tài sản trí tuệ và quyền riêng tư.

PostgreSQL: Quản lý cơ sở dữ liệu quan hệ cốt lõi (thông tin người dùng, lớp học, bảng điểm) nhằm đảm bảo tính toàn vẹn dữ liệu (ACID) và khả năng truy vấn phân tích phức tạp.

Containerization & Serverless: Các microservices đòi hỏi nhiều tài nguyên xử lý (ví dụ: Parser Agent dùng để đọc và bóc tách đề thi) được đóng gói qua Docker và triển khai trên Cloud Run. Kiến trúc serverless này giúp hệ thống tự động co giãn (auto-scaling) tức thời để xử lý các đợt lưu lượng truy cập tăng đột biến (như mùa thi cử) mà vẫn tối ưu được chi phí hạ tầng.

### 3.3 Công nghệ phát triển

#### 3.3.1. Kiến trúc Backend & Grading Engine

Core API (NestJS): Đóng vai trò là API Gateway và quản lý logic nghiệp vụ. NestJS mang lại kiến trúc module hóa chặt chẽ, dễ dàng mở rộng.

Grading Engine Độc lập (Python Microservice): Để khắc phục điểm yếu tính toán của LLM, chúng tôi xây dựng một microservice riêng biệt sử dụng thư viện SymPy để chấm điểm các biểu thức toán học. Môi trường này được cô lập hoàn toàn trong Code Execution Sandbox (Docker), đảm bảo an toàn bảo mật và tính chính xác tuyệt đối.

#### 3.3.2 Nền tảng Frontend

Web App (React / Next.js): Nền tảng ưu tiên hàng đầu trong giai đoạn MVP. Next.js cung cấp hiệu năng cao và SEO tốt, đồng thời mang lại không gian màn hình đủ lớn để kiến tạo môi trường "giả lập phòng thi" (với đồng hồ đếm ngược, phân chia khối câu hỏi) một cách chân thực nhất.
Mobile App (Kotlin): Nền tảng phụ trợ, tối ưu hóa cho trải nghiệm học tập di động (Microlearning). Tận dụng phần cứng camera để học sinh quét ảnh đề thi nhanh chóng và theo dõi lộ trình tiến bộ mọi lúc, mọi nơi.

### 3.4. Điểm mạnh cạnh tranh

Tối ưu hóa chi phí: Cung cấp giải pháp học tập chất lượng cao với mức chi phí từ thấp đến rất thấp, giúp mọi học sinh đều có thể tiếp cận được "gia sư AI" riêng biệt mà không gặp rào cản về tài chính.

Nguồn học liệu vô tận: Tận dụng công nghệ Generative AI để sản xuất đề thi mới liên tục, đảm bảo nguồn bài tập phong phú, không trùng lặp và bám sát cấu trúc đề thi thực tế.

Môi trường giả lập thi thật: Xây dựng không gian luyện thi ảo với áp lực thời gian và quy trình làm bài như kỳ thi chính thức

Đánh giá năng lực đầu vào: Hệ thống tự động kiểm tra và phân tích trình độ hiện tại của học sinh ngay từ khi bắt đầu, đảm bảo điểm xuất phát của lộ trình luôn phù hợp với năng lực thực tế.

Cá nhân hóa lộ trình học tập: Tối ưu hóa kết quả học tập bằng cách thiết kế lộ trình riêng biệt cho từng cá nhân, tập trung xoáy sâu vào các lỗ hổng kiến thức và phát huy tối đa thế mạnh của mỗi học sinh, từ đó đưa ra các đề xuất và khuyến khích sự tự học của các em.

### 4. Đối tượng sử dụng
Học sinh THPT (lớp 10 – 12) cần một trợ lý AI cá nhân để tối ưu hóa lộ trình học tập và rèn luyện kỹ năng thông qua hệ thống đề thi tạo sinh (generative) kết hợp cùng kho đề thực tế từ các trường qua từng năm.

### 5. Tính khả thi

#### 5.1. Kế hoạch phát triển
Kế hoạch phát triển trong thời gian hackathon, timeline phát triển của sản phẩm sau này, tính khả thi khi áp dụng vào thực tế,...

1. Giai đoạn Hackathon (Tháng 04-05/2026)

Vòng 1 - Khởi tạo & Đề xuất kiến trúc (Đến 02/04): Hoàn thiện ý tưởng cốt lõi và thiết kế bản vẽ hệ thống (System Design) cho kiến trúc Multi-Agent. Thiết lập sơ đồ luồng dữ liệu kết hợp giữa logic tạo sinh của LLM và mô hình đánh giá năng lực BKT (Bayesian Knowledge Tracing) để tạo ra lộ trình học tập cá nhân hóa chuẩn xác nhất.

Vòng 2 - Phát triển MVP Prototype (05/04 - 19/04): Tiến hành coding mã nguồn lõi. Tập trung triển khai luồng giao tiếp bất đồng bộ giữa 4 Agent (Manager, Parser, Teacher, Verifier) trên backend NestJS. Tích hợp các mô hình open-source (Qwen, Gemma) lên máy chủ GPU nội địa và xây dựng giao diện ứng dụng cơ bản bằng Kotlin. Đảm bảo luồng người dùng cốt lõi: Nộp ảnh đề thi → AI chấm điểm → Sinh lộ trình ôn tập hoạt động trơn tru.

Vòng 3 - Hoàn thiện & Tối ưu hóa (19/04 - 19/05): Chạy thực nghiệm với các bài thi thật để tinh chỉnh (fine-tuning) cơ chế phản biện của Verifier Agent nhằm giảm thiểu tối đa "hallucination". Tối ưu hóa độ trễ API, cải thiện chất lượng truy xuất RAG và vá lỗi (bug fixing) dựa trên các kịch bản sử dụng thực tế (edge cases) để chuẩn bị một bản demo hoàn hảo cho vòng chung kết.

2. Giai đoạn sau cuộc thi (Dài hạn)

Phát triển thêm các tính năng khác, ví dụ: Thiết lập hệ thống thi đấu (Contest) định kỳ dựa trên đề thi AI tạo sinh; tích hợp các cơ chế thúc đẩy học tập như chuỗi rèn luyện (Streak), huy hiệu (Badge) và hệ thống tích điểm đổi thưởng; đồng thời bổ sung bản đồ nhiệt (Knowledge Heatmap) phân tích lỗ hổng kiến thức, Smart Flashcards tự động tạo từ các lỗi sai.
 Xây dựng cộng đồng: Thiết lập kho lưu trữ học liệu mở, nơi học sinh có thể chia sẻ đề thi từ các trường THPT trên toàn quốc và nhận phản hồi trực tiếp từ AI cá nhân. Đồng thời, thiết lập diễn đàn cộng đồng để hỗ trợ giải đáp kỹ thuật và tạo không gian cho học sinh kết nối, trao đổi kiến thức học thuật.
Đa nền tảng: Hoàn thiện ứng dụng trên các nền tảng di động (iOS/Android) để hỗ trợ học sinh học tập mọi lúc, mọi nơi.

3. Tính khả thi của dự án:

Khả thi về Thị trường và Nguồn dữ liệu: Tệp khách hàng mục tiêu là học sinh THPT – một thị trường ngách quy mô lớn, tiềm năng và luôn được "làm mới" mỗi năm, đảm bảo vòng đời sản phẩm bền vững. Bên cạnh đó, hệ thống giáo dục Việt Nam sở hữu kho dữ liệu đề thi, học liệu (datasets) vô cùng dồi dào. Đây là nguồn tài nguyên RAG chất lượng cao giúp hệ thống AI liên tục cập nhật kiến thức, bám sát cấu trúc đề thi thực tế và linh hoạt thích ứng với Chương trình Giáo dục phổ thông mới (2018).
Khả thi về công nghệ: Sự trưởng thành của các mô hình LLM/VLM mã nguồn mở hiện nay hoàn toàn đáp ứng được các bài toán suy luận phức tạp. Hơn nữa, việc áp dụng kiến trúc Đa tác tử phân cấp (Multi-Agent System) với cơ chế phản biện chéo (Verifier) giúp khắc phục triệt để rào cản lớn nhất của AI giáo dục là hiện tượng "ảo giác" (hallucination), đảm bảo đầu ra chuẩn xác, đáng tin cậy.
Khả thi về Kinh tế và Vận hành: Nhờ chiến lược triển khai hạ tầng linh hoạt (Hybrid Cloud) kết hợp giữa tài nguyên máy chủ nội địa và đám mây serverless, hệ thống tối ưu hóa được tối đa chi phí vận hành. Điều này mang lại lợi thế cạnh tranh tuyệt đối về giá, cho phép cung cấp một "Gia sư AI 24/7" toàn diện với chi phí rẻ hơn rất nhiều so với phương pháp học thêm truyền thống, mở ra cơ hội bình đẳng trong giáo dục cho mọi học sinh.
## 5.2. Ngân sách dự kiến
GPU Server: Sử dụng gói thuê GPU H100 tteen FPT AI Cloud đóng vai trò như một Self-Hosting GPU Server. Với nguồn kinh phí được hỗ trợ từ GDGoC x FPT.
Mô hình AI: Sử dụng các open-source model được public trên HuggingFace nhằm tối ưu Latency, Price và tăng khả năng scaling của dự án. Các models dự kiến như sau:
Manager: Qwen3-8B và Gemini 2.5 Flash  
Teacher: Qwen3-14B Quantized
Verifier: Gemma 3 4B 
Parser: PaddleOCR hoặc là DeepseekOCR
Như vậy, toàn bộ kinh phí để duy trì, phát triển và triển khai của dự án gần như là miễn phí.
6. Tài liệu tham khảo
Thakur, A. S., Choudhary, K., Ramayapally, V. S., Vaidyanathan, S., & Hupkes, D. (2025). Judging the Judges: Evaluating Alignment and Vulnerabilities in LLMs-as-Judges. Proceedings of the 5th Workshop on Generation Evaluation and Metrics (GEM). Association for Computational Linguistics. https://aclanthology.org/2025.gem-1.33/

Zhuang, Y., Yu, Y., Wang, K., Sun, H., & Zhang, C. (2023). ToolQA: A Dataset for LLM Question Answering with External Tools. Advances in Neural Information Processing Systems, 36 (Datasets and Benchmarks Track). https://proceedings.neurips.cc/paper_files/paper/2023/hash/9cb2a7495900f8b602cb10159246a016-Abstract-Datasets_and_Benchmarks.html
7. Thông tin liên hệ 
Nguyễn Phúc Khang - nguyenphuc.khang110806@gmail.com - 0352778180
Lê Hữu Nguyên Huy - lehuunguyenhuy@gmail.com - 0384044833
Võ Quang Phúc - phucvo370206@gmail.com - 0772644918
Trương Đình Nhật Huy - nagahao123@gmail.com - 0335570346


