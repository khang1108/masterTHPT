Chương này hệ thống hoá các khái niệm cơ bản về hàm số và đồ thị của hàm số đã được học ở các lớp dưới; cách vẽ đồ thị của hàm số bậc hai; xét dấu của tam thức bậc hai và vận dụng để giải bất phương trình bậc hai, bài toán thực tiến. Ta cũng xét các phương trình chứa căn thức đơn giản có thể quy về phương trình bậc hai.

# HÀM SỐ

# THUẬT NGỮ

- Tập xác định
- Tập giá trị
- Đồ thi của hàm số
- Hàm số đồng biến
- · Hàm số nghịch biến

# KIẾN THỰC, KĨ NĂNG

- Nhận biết những mô hình dẫn đến khái niệm hàm số.
- Mô tả các khái niệm cơ bản về hàm số: định nghĩa hàm số, tập xác định, tập giá trị, hàm số đồng biến, hàm số nghich biến, đồ thi của hàm số.
- · Mô tả dạng đồ thị của hàm số đồng biến, nghịch biến.
- Vận dụng kiến thức của hàm số vào giải quyết một số bài toán thực tiễn.

Quan sát hoá đơn tiền điện ở hình bên. Hãy cho biết tổng lượng điện tiêu thụ trong tháng và số tiền phải trả (chưa tính thuế giá trị gia tăng).

Có cách nào mô tả sự phụ thuộc của số tiền phải trả vào tổng lượng điện tiêu thụ hay không?

| ST: 010092009<br>ài khoản số: 1<br>ên khách háng<br>(a chỉ KH:Cụm<br>lã khách hàng | 09.1 - P502      | Tại:          | Tit ngày:      |                         | lến ngày: 28/02/2    |
|------------------------------------------------------------------------------------|------------------|---------------|----------------|-------------------------|----------------------|
| Chỉ số cũ<br>kw                                                                    | Chỉ số mới<br>kw | Số dùng<br>kw | DN TT          | Dơn giá                 | Thành tiến           |
| 4334                                                                               | 4452             | 118           | kw             | d/kwh                   | (Amount)             |
| Ngày 1 Tháng 3 năm 2021                                                            |                  | Trong đó      | 50<br>50<br>18 | 1 678<br>1 734<br>2 014 | 83 9<br>86 7<br>36 2 |
|                                                                                    |                  | Cộng:         |                |                         | 206 8                |
|                                                                                    |                  | Thuế GTGT 10  | 1%:            |                         | 20 6                 |
|                                                                                    |                  | Tổng tiến tha | nh toán:       |                         | 227 5                |

# 1. KHÁI NIÊM HÀM SỐ

H91. Bảng 6.1 cho biết nồng độ bụi PM 2.5 trong không khí theo thời gian trong ngày 25-3-2021 tại một trạm quan trắc ở Thủ đô Hà Nội:

| Thời điểm (giờ)               | 0     | 4     | 8    | 12    | 16    |
|-------------------------------|-------|-------|------|-------|-------|
| Nồng độ bụi PM<br>2.5 (µg/m³) | 74,27 | 64,58 | 57,9 | 69,07 | 81,78 |

Bụi PM 2.5 là hạt bụi mịn có đường kính nhỏ hơn 2,5 micrômét, gây tác hại cho sức khoẻ.

## Bảng 6.1 (Theo moitruongthudo.vn)

- a) Hãy cho biết nồng độ bụi PM 2.5 tại mỗi thời điểm 8 giờ, 12 giờ, 16 giờ.
- b) Trong Bảng 6.1, mỗi thời điểm tương ứng với bao nhiều giá trị của nồng độ bụi PM 2.5?

![](_page_5_Picture_7.jpeg)

## HD2. Quan sát Hình 6.1.

- a) Thời gian theo dối mực nước biển ở Trường Sa được thể hiện trong hình từ năm nào đến năm nào?
- b) Trong khoảng thời gian đó, năm nào mực nước biển trung bình tại Trường Sa cao nhất, thấp nhất?

![](_page_5_Figure_11.jpeg)

Hình 6.1 (Theo Tổng cực Thống kê)

## HĐ3. Tính tiền điện

 a) Dựa vào Bảng 6.2 về giá bán lẻ điện sinh hoạt, hãy tính số tiền phải trả ứng với mỗi lượng điện tiêu thụ ở Bảng 6.3:

| Lượng điện<br>tiêu thụ (kWh) | 50 | 100 | 200 |
|------------------------------|----|-----|-----|
| Số tiền<br>(nghìn đồng)      | ?  | ?   | ?   |

Bảng 6.3

| Mức điện tiêu thụ               | Giá bán điện<br>(đồng/kWh) |
|---------------------------------|----------------------------|
| Bậc 1 (từ 0 đến 50 kWh)         | 1 678                      |
| Bậc 2 (từ trên 50 đến 100 kWh)  | 1 734                      |
| Bậc 3 (từ trên 100 đến 200 kWh) | 2 014                      |
| Bậc 4 (từ trên 200 đến 300 kWh) | 2 536                      |
| Bậc 5 (từ trên 300 đến 400 kWh) | 2 834                      |
| Bậc 6 (từ trên 400 kWh trở lên) | 2 927                      |

Bảng 6.2 (Theo *Tập đoàn Điện lực Việt Nam ngày 20-3-2019*)

b) Gọi x là lượng điện tiêu thụ (đơn vị kVVh) và y là số tiền phải trả tương ứng (đơn vị nghìn đồng). Hãy viết công thức mô tả sự phụ thuộc của y vào x khi  $0 \le x \le 50$ .

kWh hay kW.h (kilôoát giờ, còn gọi là số điện) là đơn vị để đo lượng điện tiêu thụ. Ví dụ, một chiếc bàn là công suất 2 kW, nếu sử dụng liên tục trong 1 giờ sẽ tiêu thụ lượng điện là 2 kWh.

Trong HĐ1, nếu gọi x là thời điểm và y là nồng độ bụi PM 2.5 thì với mỗi giá trị của x, xác định được chỉ một giá trị tương ứng của y. Ta tìm thấy mối quan hệ phụ thuộc tương tự giữa các đại lượng trong HĐ2, HĐ3.

![](_page_5_Picture_22.jpeg)

Giả sử có đại lượng y phụ thuộc vào đại lượng thay đổi x, trong đó x nhân giá trị thuộc tập hợp số D.

Nếu với mỗi giá trị của x thuộc tập hợp số D có một và chỉ một giá trị tương ứng của y thuộc tập số thực  $\mathbb R$  thì ta có một hàm số.

Ta gọi x là biến số và y là hàm số của x.

Tập hợp D gọi là tập xác định của hàm số.

Tập tất cả các giá trị y nhận được, gọi là tập giá trị của hàm số.

Khi y là hàm số của x, ta có thể viết y = f(x), y = g(x), ...

![](_page_6_Picture_5.jpeg)

Ví dụ 1. Trong HĐ1, nếu gọi x là thời điểm, y là nồng độ bụi PM 2.5 thì x là biến số và y là hàm số của x. Đó là hàm số được cho bằng bảng.

Tập xác định của hàm số là  $D = \{0, 4, 8, 12, 16\}$ .

Tập giá trị của hàm số là {74,27; 64,58; 57,9; 69,07; 81,78}.

Ví dụ 2. Viết hàm số mô tả sự phụ thuộc của quãng đường đi được vào thời gian của một vật chuyển động thẳng đều với vận tốc 2 m/s. Tìm tập xác định của hàm số đó. Tính quãng đường vật đi được sau 5 s, 10 s.

#### Giải

Một vật chuyển động thẳng đều với vận tốc v = 2 m/s thì quãng đường đi được S (mét) phụ thuộc vào thời gian t (giây) theo công thức S = 2t, trong đó t là biến số, S = S(t) là hàm số của t. Tập xác định của hàm số là  $D = [0; +\infty)$ .

Quãng đường vật đi được sau 5 s là:  $S_1 = S(5) = 2.5 = 10$  (m).

Quãng đường vật đi được sau 10 s là:  $S_2 = S(10) = 2.10 = 20$  (m).

Chú ý. Khi cho hàm số bằng công thức y = f(x) mà không chỉ rõ tập xác định của nó thì ta quy ước tập xác định của hàm số là tập hợp tất cả các số thực x sao cho biểu thức f(x) có nghĩa.

> Ví dụ 3. Tìm tập xác định của các hàm số sau:

a) 
$$y = \sqrt{2x - 4}$$
;

b) 
$$y = \frac{1}{x-1}$$
.

#### Giai

a) Biểu thức  $\sqrt{2x-4}$  có nghĩa khi  $2x-4 \ge 0$ , tức là khi  $x \ge 2$ .

Vậy tập xác định của hàm số đã cho là  $D = [2; +\infty)$ .

b) Biểu thức  $\frac{1}{x-1}$  có nghĩa khi  $x-1\neq 0$ , tức là khi  $x\neq 1$ .

Vậy tập xác định của hàm số đã cho là  $D = \mathbb{R} \setminus \{1\}$ .

Luyện tập 1. a) Hãy cho biết Bảng 6.4 có cho ta một hàm số hay không. Nếu có, tìm tập xác định và tập giá trị của hàm số đó.

| Thời điểm (năm)                               | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 |
|-----------------------------------------------|------|------|------|------|------|------|
| Tuổi thọ trung bình của người Việt Nam (tuổi) | 73,1 | 73,2 | 73,3 | 73,4 | 73,5 | 73,5 |

## Bảng 6.4 (Theo Tổng cực Thống kê)

- b) Trở lại HĐ2, ta có hàm số cho bằng biểu đồ. Hãy cho biết giá trị của hàm số tại x = 2018. Tìm tập xác định, tập giá trị của hàm số đó.
- c) Cho hàm số  $y = f(x) = -2x^2$ . Tính f(1); f(2) và tìm tập xác định, tập giá trị của hàm số này.

Nhận xét. Một hàm số có thể được cho bằng bảng, bằng biểu đồ, bằng công thức hoặc bằng mô tả.

# 2. ĐỔ THI CỦA HÀM SỐ

**)** H94. Quan sát Hình 6.2 và cho biết những điểm nào sau đây nằm trên đồ thị của hàm số  $y = \frac{1}{2}x^2$ :

$$(0; 0), (2; 2), (-2; 2), (1; 2), (-1; 2).$$

Nêu nhân xét về mối quan hệ giữa hoành đô và tung đô của những điểm nằm trên đồ thi.

Đồ thị của hàm số y = f(x) xác định trên tập D là tập hợp tất cả các điểm M(x; f(x)) trên mặt phẳng toa đô với mọi x thuộc D.

![](_page_7_Figure_5.jpeg)

![](_page_7_Figure_6.jpeg)

## Hình 6.2

# Giài

Công thức của hàm số cho ở HĐ3b là y = 1,678x với  $0 \le x \le 50$ .

Tập xác định của hàm số này là D = [0; 50].

Vì 
$$0 \le x \le 50$$
 nên  $0 \le y \le 1,678 \cdot 50 = 83,9$ .

Vậy tập giá trị của hàm số là [0; 83,9].

Đồ thị của hàm số y = 1,678x trên [0; 50] là một đoạn thẳng (H.6.3).

![](_page_7_Figure_14.jpeg)

## Luyện tập 2

- a) Dựa vào đồ thị của hàm số  $y = \frac{1}{2}x^2$  (H.6.2), tìm x sao cho y = 8.
- b) Vẽ đồ thị của các hàm số y = 2x + 1 và  $y = 2x^2$  trên cùng một mặt phẳng toạ độ.
- **⋙ Vận dụng 1.** Nếu lượng điện tiêu thụ từ trên 50 đến 100 kWh (50 < x ≤ 100) thì công thức liên hệ giữa y và x đã thiết lập ở HĐ3 không còn đúng nữa.

Theo bảng giá bán lẻ điện sinh hoạt (Bảng 6.2) thì số tiền phải trả là:

$$y = 1,678.50 + 1,734(x - 50) = 83.9 + 1,734(x - 50)$$
, hay  $y = 1,734x - 2.8$  (nghìn đồng).

Vậy trên tập xác định D = (50; 100], hàm số y mô tả số tiền phải thanh toán có công thức là y = 1,734x - 2,8; tập giá trị của nó là (83,9; 170,6].

Hãy vẽ đồ thị ở Hình 6.3 vào vở rồi vẽ tiếp đồ thị của hàm số y = 1,734x - 2,8 trên tập D = (50; 100].

## ⊸ Tìm hiểu thêm ∘

Hàm số mô tả sự phụ thuộc của y (số tiền phải trả) vào x (lượng điện tiêu thụ) trên từng khoảng giá trị x được cho bằng công thức như sau:

$$y = \begin{cases} 1,678x & \text{n\'eu} & 0 \le x \le 50 \\ 1,734x - 2,8 & \text{n\'eu} & 50 < x \le 100 \\ 2,014x - 30,8 & \text{n\'eu} & 100 < x \le 200 \\ 2,536x - 135,2 & \text{n\'eu} & 200 < x \le 300 \\ 2,834x - 224,6 & \text{n\'eu} & 300 < x \le 400 \\ 2,927x - 261,8 & \text{n\'eu} & x > 400 \end{cases}$$

Đồ thi của hàm số trên được vẽ như Hình 6.4.

![](_page_7_Figure_27.jpeg)

# 3. SƯ ĐỒNG BIẾN, NGHICH BIẾN CỦA HÀM SỐ

**>> HD5.** Cho hàm số y = -x + 1 và y = x. Tính giá trị y theo giá trị x để hoàn thành bảng sau:

| Х                   | -2 | -1 | 0 | 1 | 2 |
|---------------------|----|----|---|---|---|
| y = -x + 1          | ?  | ?  | ? | ? | ? |
| <i>y</i> = <i>x</i> | ?  | ?  | ? | ? | ? |

Khi giá trị x tăng, giá trị y tương ứng của mỗi hàm số y = -x + 1 và y = x tăng hay giảm?

- **15** HD6. Quan sát đồ thị của hàm số  $y = f(x) = -x^2$  trên  $\mathbb{R}$  (H.6.5). Hỏi:
  - a) Giá trị của f(x) tăng hay giảm khi x tăng trên khoảng  $(-\infty; 0)$ ?
  - b) Giá tri của f(x) tăng hay giảm khi x tăng trên khoảng  $(0; +\infty)$ ?

![](_page_8_Figure_7.jpeg)

Hình 6.5

Hàm số y = f(x) được gọi là đồng biến (tăng) trên khoảng (a; b), nếu

$$\forall x_1, x_2 \in (a; b), x_1 < x_2 \Rightarrow f(x_1) < f(x_2).$$

Hàm số y = f(x) được gọi là nghịch biến (giảm) trên khoảng (a; b), nếu

$$\forall x_1, x_2 \in (a; b), \ x_1 < x_2 \Rightarrow f(x_1) > f(x_2).$$

**)** Ví dụ 5. Hàm số  $y = x^2$  đồng biến hay nghịch biến trên mỗi khoảng:  $(-\infty; 0)$  và  $(0; +\infty)$ ? Giải

Vẽ đồ thị hàm số  $y = f(x) = x^2$  như Hình 6.6.

- Trên khoảng (-∞;0), đồ thị "đi xuống" từ trái sang phải và với  $x_1, x_2 \in (-\infty, 0), x_1 < x_2$  thì  $f(x_1) > f(x_2)$ . Như vậy, hàm số  $y = x^2$  nghịch biến trên khoảng  $(-\infty, 0)$ .
- Trên khoảng (0; +∞), đồ thị "đi lên" từ trái sang phải và với  $X_3, X_4 \in (0, +\infty), X_3 < X_4 \text{ thì } f(X_3) < f(X_4). \text{ Như vậy, hàm số}$  $y = x^2$  đồng biến trên khoảng (0;  $+\infty$ ).

![](_page_8_Figure_17.jpeg)

Hình 6.6

## Chú ý

- Đồ thị của một hàm số đồng biến trên khoảng (a; b) là đường "đi lên" từ trái sang phải;
- Đồ thị của một hàm số nghịch biến trên khoảng (a; b) là đường "đi xuống" từ trái sang phải.

- **Luyện tập 3.** Vẽ đồ thị của hàm số y = 3x + 1 và  $y = -2x^2$ . Hãy cho biết:
  - a) Hàm số y = 3x + 1 đồng biến hay nghịch biến trên  $\mathbb{R}$ .
  - b) Hàm số  $y = -2x^2$  đồng biến hay nghịch biến trên mỗi khoảng:  $(-\infty; 0)$  và  $(0; +\infty)$ .
- >> Vân dung 2. Quan sát bảng giá cước taxi bốn chỗ trong Hình 6.7.
  - a) Tính số tiền phải trả khi di chuyển 25 km.
  - b) Lập công thức tính số tiền cước taxi phải trả theo số kilômét di chuyển.
  - c) Vẽ đồ thị và cho biết hàm số đồng biến trên khoảng nào, nghịch biến trên khoảng nào.

| Giá mở cửa                  | Giá km tiếp theo               | Tử km thứ 25                |
|-----------------------------|--------------------------------|-----------------------------|
| Commencement rate up 0.6 km | From the following km to 25 km | For each km from the 25 km+ |
| 10.000 đ/0.6km              | 13.000 đ/km                    | 11.000 đ/km                 |

Hình 6.7

# **BÀI TÂP**

6.1. Xét hai đại lượng x, y phụ thuộc vào nhau theo các hệ thức dưới đây. Những trường hợp nào thì y là hàm số của x?

a) 
$$x + y = 1$$

b) 
$$v = x^2$$
:

c) 
$$v^2 = x$$

a) 
$$x + y = 1$$
; b)  $y = x^2$ ; c)  $y^2 = x$ ; d)  $x^2 - y^2 = 0$ .

- 6.2. Hãy cho một ví du về hàm số được cho bằng bảng hoặc biểu đồ. Hãy chỉ ra tập xác định và tập giá tri của hàm số đó.
- 6.3. Tìm tập xác định của các hàm số sau:

a) 
$$y = 2x^3 + 3x + 1$$
;

b) 
$$y = \frac{x-1}{x^2 - 3x + 2}$$
; c)  $y = \sqrt{x+1} + \sqrt{1-x}$ .

c) 
$$y = \sqrt{x+1} + \sqrt{1-x}$$

6.4. Tìm tập xác định và tập giá trị của mỗi hàm số sau:

a) 
$$y = 2x + 3$$
;

b) 
$$y = 2x^2$$
.

**6.5.** Vẽ đồ thị các hàm số sau và chỉ ra các khoảng đồng biến, nghịch biến của chúng. a) y = -2x + 1; b)  $y = -\frac{1}{2}x^2$ .

a) 
$$y = -2x + 1$$

b) 
$$y = -\frac{1}{2}x^2$$
.

- 6.6. Giá thuê xe ô tô tự lái là 1,2 triệu đồng một ngày cho hai ngày đầu tiên và 900 nghìn đồng cho mỗi ngày tiếp theo. Tổng số tiền T phải trả là một hàm số của số ngày x mà khách thuê xe.
  - a) Viết công thức của hàm số T = T(x).
  - b) Tính T(2), T(3), T(5) và cho biết ý nghĩa của mỗi giá trị này.

## Em có biết?

## HÀM SỐ VÀ MÔ HÌNH HOÁ

Nhiều tình huống trong thực tiến đời sống hoặc trong khoa học liên quan đến việc tìm hiểu một đại lượng thay đổi phụ thuộc vào một đại lượng khác như thế nào. Việc tìm hàm số mô tả sư phu thuộc của đại lượng này vào đại lượng kia được gọi là *mô hình* hoá. Ta thường sử dụng những tính chất hình học hoặc tính chất đại số của đối tương cần nghiên cứu để thiết lập mô hình. Dựa vào mô hình đã được thiết lập, ta có thể phân tích và dư đoán các tính chất của đối tương hoặc của tình huống cần nghiên cứu.

Quá trình mô hình hoá bằng cách dùng hàm số thường bao gồm các bước sau:

## Bước 1: Diễn tả mô hình bằng lời

Xác định đại lượng cần mô hình hoá và diễn tả bằng lời sự phụ thuộc của nó vào những đại lượng khác trong bài toán.

## Bước 2: Chọn biến số

Xác định tất cả các đại lượng được dùng để diễn tả sự phụ thuộc bằng lời ở Bước 1. Dùng kí hiệu, chẳng hạn x, để chỉ một đại lượng thích hợp nào đó và biểu diễn các đại lượng khác theo x.

## Bước 3: Thiết lập mô hình

Biểu diễn sự phụ thuộc ở Bước 1 như là một hàm số của biến số x đã được chọn ở Bước 2.

## Bước 4: Sử dụng mô hình

Sử dụng hàm số đã thiết lập ở Bước 3 để trả lời các câu hỏi của bài toán.

Kiểm tra sự phù hợp của mô hình.

Dưới đây ta xét một ví dụ đơn giản minh hoạ cho quá trình mô hình hoá này.

Ví dụ. Bác An dùng 20 m lưới thép gai rào thành một mảnh vườn hình chữ nhật để trồng rau.

- a) Thiết lập hàm số mô tả diện tích của mảnh vườn.
- b) Bác An có thể rào thành mảnh vườn có diện tích bằng 21 m² được không?
- c) Chiều rộng của mảnh vườn phải như thế nào để diện tích của mảnh vườn lớn hơn 24 m²?
- d) Tìm kích thước của mảnh vườn hình chữ nhật có diện tích lớn nhất mà bác An có thể rào được.

10 - x

### Giải

Bước 1. Diễn tả mô hình bằng lời

Ta biết rằng

Diện tích mảnh vườn hình chữ nhật = chiều rộng x chiều dài.

Bước 2. Chon biến số

Có hai đại lượng thay đổi là chiều rộng và chiều dài. Vì ta muốn lập hàm số chỉ phụ thuộc vào một biến số ta chọn, chẳng hạn

x = chiều rộng của mảnh vườn hình chữ nhật.

Ta cần tính chiều dài của mảnh vườn hình chữ nhật theo x. Do chu vi của mảnh vườn hình chữ nhật không đổi bằng 20 m và nửa chu vi bằng tổng của chiều rộng và chiều dài nên chiều dài của mảnh vườn sẽ là 10 - x (m).

Bước 3. Thiết lập mô hình

Diên tích của mảnh vườn hình chữ nhật là

$$S(x)$$
 = chiều rộng x chiều dài =  $x(10 - x) = -x^2 + 10x$  (m).

Như vậy, ở đây diện tích S(x) của mảnh vườn là hàm số của chiều rộng x.

Bước 4. Sử dụng mô hình

Ta có thể sử dụng mô hình đã thiết lập để trả lời các câu hỏi ở phần b, c, d. Chẳng hạn, với câu hỏi ở phần b, ta cần tìm chiều rộng x của mảnh vườn sao cho

$$S(x) = 21 \text{ hay } -x^2 + 10x = 21, \text{ hay } x^2 - 10x + 21 = 0.$$

Giải phương trình bậc hai này ta được hai nghiệm x = 3 và x = 7.

Vì chiều rộng phải nhỏ hơn hoặc bằng chiều dài nên chỉ có nghiệm x = 3 là thoả mãn. Khi đó mảnh vườn hình chữ nhật có chiều rộng là 3 m và chiều dài là 10 - 3 = 7 (m).

Vậy bác An có thể dùng 20 m hàng rào dây thép gai để rào thành mảnh vườn hình chữ nhật có diện tích bằng  $21~\text{m}^2$ .

Trong các bài sau, các em sẽ được học những kiến thức toán học cần thiết để sử dụng hàm số S(x) trả lời cho các câu hỏi ở phần c và phần d.

# HÀM SỐ BẬC HAI

## THUẬT NGỮ

- · Hàm số bậc hai
- · Bảng giá trị
- Parabol
- Định
- Trục đối xứng

# KIẾN THỨC, KĨ NĂNG

- · Nhân biết hàm số bậc hai.
- Thiết lập bảng giá trị của hàm số bậc hai.
- Vẽ parabol (parabola) là đồ thị của hàm số bậc hai.
- Nhận biết các yếu tố cơ bản của đường parabol như đình, truc đối xứng.
- Nhận biết và giải thích các tính chất của hàm số bậc hai thông qua đồ thị.
- Vận dụng kiến thức về hàm số bậc hai và đồ thị vào giải quyết bài toán thực tiễn.

Bác Việt có một tấm lưới hình chữ nhật dài 20 m. Bác muốn dùng tấm lưới này rào chắn ba mặt áp bên bờ tường của khu vườn nhà mình thành một mảnh đất hình chữ nhật để trồng rau.

Hỏi hai cột góc hàng rào cần phải cắm cách bờ tường bao xa để mảnh đất được rào chắn của bác có diện tích lớn nhất?

![](_page_11_Picture_17.jpeg)

Hình 6.8

# 1. KHÁI NIỆM HÀM SỐ BẬC HẠI CỤ Ố C SỐNG

- **>> H91.** Xét bài toán rào vườn ở tình huống mở đầu. Gọi x mét (0 < x < 10) là khoảng cách từ điểm cắm cọc đến bờ tường (H.6.8). Hấy tính theo x:
  - a) Độ dài cạnh PQ của mảnh đất.
  - b) Diện tích S(x) của mảnh đất được rào chắn.

 $\vec{O}$  đây ta tính được  $S(x) = -2x^2 + 20x$ .

Đây là một hàm số cho bởi công thức và gọi là một hàm số bậc hai của biến số x.

Tổng quát, ta có

Hàm số bậc hai là hàm số cho bởi công thức

$$y = ax^2 + bx + c,$$

trong đó x là biến số, a, b, c là các hằng số và  $a \neq 0$ .

Tập xác định của hàm số bậc hai là  $\mathbb{R}$ .

![](_page_12_Picture_0.jpeg)

A Hàm số nào dưới đây là hàm số bậc hai?

**A.** 
$$y = x^4 + 3x^2 + 2$$
.

**B.** 
$$y = \frac{1}{x^2}$$

C. 
$$y = -3x^2 + 1$$

A. 
$$y = x^4 + 3x^2 + 2$$
. B.  $y = \frac{1}{x^2}$ . C.  $y = -3x^2 + 1$ . D.  $y = 3\left(\frac{1}{x}\right)^2 + 3\frac{1}{x} - 1$ .

## Nhân xét.

Hàm số  $y = ax^2$  ( $a \neq 0$ ) đã học ở lớp 9 là một trường hợp đặc biệt của hàm số bậc hai với b=c=0

**)** Ví du 1. Xét hàm số bậc hai  $y = -2x^2 + 20x$ . Thay dấu "?" bằng các số thích hợp để hoàn thành bảng giá trị sau của hàm số.

| Χ | 0 | 2 | 4 | 5 | 6 | 8 | 10 |
|---|---|---|---|---|---|---|----|
| V | ? | ? | ? | ? | ? | ? | ?  |

Bảng giá tri của hàm số  $v = -2x^2 + 20x$  tai một số điểm.

## Giài

Thay các giá trị của x vào công thức hàm số, ta được:

| Х | 0 | 2  | 4  | 5  | 6  | 8  | 10 |
|---|---|----|----|----|----|----|----|
| У | 0 | 32 | 48 | 50 | 48 | 32 | 0  |

![](_page_12_Picture_14.jpeg)

- **Luyên tập 1.** Cho hàm số y = (x 1)(2 3x).
  - a) Hàm số đã cho có phải là hàm số bậc hai không? Nếu có, hãy xác định các hệ số a, b, c của nó.
  - b) Thay dấu "?" bằng các số thích hợp để hoàn thành bảng giá trị sau của hàm số đã cho.

| Х | <b>-</b> 2 | -1 | 0 | 1 |
|---|------------|----|---|---|
| У | ?          | ?  | ? | ? |

- **>> Vận dụng 1.** Một viên bi rơi tự do từ độ cao 19,6 m xuống mặt đất. Độ cao *h* (mét) so với mặt đất của viên bị trong khi rơi phụ thuộc vào thời gian t (giây) theo công thức:  $h = 19.6 - 4.9t^2$ ;  $h, t \geq 0$ .
  - a) Hỏi sau bao nhiêu giây kể từ khi rơi viên bị chạm đất?
  - b) Tìm tập xác định và tập giá trị của hàm số h.

# 2. ĐỔ THI CỦA HÀM SỐ BẬC HAI

Ở lớp 9, ta đã biết dạng đồ thị của hàm số  $y = ax^2 (a \neq 0)$  (H.6.9). Trong muc này ta sẽ tìm hiểu đồ thị của hàm số bậc hai  $y = ax^2 + bx + c (a \neq 0).$ 

![](_page_12_Figure_24.jpeg)

![](_page_12_Figure_25.jpeg)

![](_page_12_Figure_26.jpeg)

Hình 6.9

- **10 H92.** Xét hàm số  $y = S(x) = -2x^2 + 20x$  (0 < x < 10).
  - a) Trên mặt phẳng toạ độ Oxy, biểu diễn toạ độ các điểm trong bảng giá trị của hàm số lập được ở Ví dụ 1. Nối các điểm đã vẽ lại ta được dạng đồ thị hàm số  $y = -2x^2 + 20x$  trên khoảng (0; 10) như trong Hình 6.10. Dạng đồ thị của hàm số  $y = -2x^2 + 20x$  có giống với đồ thị của hàm số  $y = -2x^2$  hay không?

- b) Quan sát dạng đồ thị của hàm số  $y = -2x^2 + 20x$  trong Hình 6.10, tìm toạ độ điểm cao nhất của đồ thi.
- c) Thực hiện phép biến đổi  $y = -2x^2 + 20x = -2(x^2 - 10x)$  $= -2(x^2 - 2 \cdot 5 \cdot x + 25) + 50 = -2(x - 5)^2 + 50.$

Hãy cho biết giá trị lớn nhất của diện tích mảnh đất được rào chắn. Từ đó suy ra lời giải của bài toán ở phần mở đầu.

![](_page_13_Figure_3.jpeg)

Hình 6.10. Dạng đồ thị của hàm số  $v = -2x^2 + 20x$ 

乃 HĐ3. Tương tự HĐ2, ta có dạng đồ thị của một số hàm số bậc hai sau.

![](_page_13_Figure_6.jpeg)

![](_page_13_Figure_7.jpeg)

![](_page_13_Figure_8.jpeg)

$$y = -2x^2 - 3x + 1$$

Từ các đồ thị hàm số trên, hãy hoàn thành bảng sau đây.

|                    |         | Tính chất của đồ thị                       |                                        |               |  |
|--------------------|---------|--------------------------------------------|----------------------------------------|---------------|--|
| Hàm số             | Hệ số a | Bề lõm của đồ thị<br>(Quay lên/Quay xuống) | Toạ độ điểm cao<br>nhất/điểm thấp nhất | Trục đối xứng |  |
| $y = x^2 + 2x + 2$ | 1       | Quay lên                                   | (–1; 1)                                | <i>x</i> = −1 |  |
| $y=-2x^2-3x+1$     | ?       | ?                                          | ?                                      | ?             |  |

Tổng quát, ta có thể viết hàm số bậc hai  $y = ax^2 + bx + c$  ( $a \neq 0$ ) dưới dạng

$$y = ax^{2} + bx + c = a\left(x^{2} + 2\frac{b}{2a}x + \frac{b^{2}}{4a^{2}}\right) - \frac{b^{2}}{4a} + c = a\left(x + \frac{b}{2a}\right)^{2} - \frac{\Delta}{4a}, \text{ V\'oi} \ \Delta = b^{2} - 4ac.$$

Ta thấy điểm  $I\left(-\frac{b}{2a}; -\frac{\Delta}{4a}\right)$  thuộc đồ thị hàm số bậc hai và là một điểm đặc biệt, nó đóng vai trò như điểm O(0;0) của đồ thị hàm số  $y=ax^2$ . Cụ thể:

- Nếu a > 0 thì  $y = a \left( x + \frac{b}{2a} \right)^2 \frac{\Delta}{4a} \ge -\frac{\Delta}{4a}$  với mọi x. Như vậy điểm l là điểm thấp nhất trên đồ thị.
- Nếu a < 0 thì  $y = a \left( x + \frac{b}{2a} \right)^2 \frac{\Delta}{4a} \le -\frac{\Delta}{4a}$  với mọi x. Như vậy điểm I là điểm cao nhất trên đồ thi.

Gọi  $(P_0)$  là parabol  $y = ax^2$ . Nếu ta "dịch chuyển"  $(P_0)$  theo vector  $\overrightarrow{Ol}$  thì ta sẽ thu được đồ thị (P) của hàm số  $y = ax^2 + bx + c$  có dạng như Hình 6.11.

![](_page_14_Figure_4.jpeg)

a) Đồ thị hàm số y = ax² + bx + c với a > 0 (trường hợp parabol cắt trục hoành)

![](_page_14_Figure_6.jpeg)

 b) Đồ thị hàm số y = ax² + bx + c với a < 0 (trường hợp parabol cắt trục hoành)

Hình 6.11

Nhận xét. Đồ thị hàm số bậc hai  $y = ax^2 + bx + c$  là một parabol.

• Đồ thị hàm số  $y = ax^2 + bx + c$  ( $a \ne 0$ ) là một đường parabol có đỉnh là điểm  $I\left(-\frac{b}{2a}; -\frac{\Delta}{4a}\right)$ , có trục đối xứng là đường thẳng  $x = -\frac{b}{2a}$ . Parabol này quay bề lõm lên trên nếu a > 0,

xuống dưới nếu a < 0.

- Để vẽ đường parabol  $y = ax^2 + bx + c$  ta tiến hành theo các bước sau:
- 1. Xác định toạ độ đỉnh  $I\left(-\frac{b}{2a}; -\frac{\Delta}{4a}\right)$ ;
- 2. Vẽ trục đối xứng  $x = -\frac{b}{2a}$ ;
- Xác định toạ độ các giao điểm của parabol với trục tung, trục hoành (nếu có) và một vài điểm đặc biệt trên parabol;
- 4. Vẽ parabol.

- **Ví du 2.** a) Vẽ parabol  $y = -2x^2 2x + 4$ .
  - b) Từ đồ thi, hãy tìm khoảng đồng biến, nghịch biến và giá tri lớn nhất của hàm số  $y = -2x^2 - 2x + 4$ .

![](_page_15_Figure_2.jpeg)

a) Ta có a = -2 < 0 nên parabol quay bề lõm xuống dưới. Đỉnh  $I\left(-\frac{1}{2}; \frac{9}{2}\right)$ . Trục đối xứng  $x = -\frac{1}{2}$ . Giao điểm của đồ thị với trục Oy là A(0; 4). Parabol cắt trục hoành tại hai điểm có hoành độ là nghiệm của phương trình  $-2x^2 - 2x + 4 = 0$ , tức là x = 1 và x = -2 (H.6.12).

![](_page_15_Figure_4.jpeg)

- Để vẽ đồ thị chính xác hơn, ta có thể lấy thêm điểm đối xứng với A qua trục đối xứng  $x = -\frac{1}{2}$  là B(-1; 4).
- b) Từ đồ thị ta thấy:
- Hàm số y =  $-2x^2 2x + 4$  đồng biến trên  $\left(-\infty; -\frac{1}{2}\right)$ , nghịch biến trên  $\left(-\frac{1}{2}; +\infty\right)$ ;
- Giá trị lớn nhất của hàm số là  $y = \frac{9}{2}$ , khi  $x = -\frac{1}{2}$ .
- **Luyện tập 2.** Vẽ parabol  $y = 3x^2 10x + 7$ . Từ đó tìm khoảng đồng biến, nghịch biến và giá trị nhỏ nhất của hàm số  $y = 3x^2 - 10x + 7$ .

Nhận xét. Từ đồ thị hàm số  $y = ax^2 + bx + c$  ( $a \ne 0$ ), ta suy ra tính chất của hàm số  $y = ax^2 + bx + c \ (a \neq 0)$ :

| Với a > 0                                                              | Với a < 0                                                             |
|------------------------------------------------------------------------|-----------------------------------------------------------------------|
| Hàm số nghịch biến trên khoảng $\left(-\infty; -\frac{b}{2a}\right)$ ; | Hàm số đồng biến trên khoảng $\left(-\infty; -\frac{b}{2a}\right)$ ;  |
| Hàm số đồng biến trên khoảng $\left(-\frac{b}{2a}; +\infty\right)$ ;   | Hàm số nghịch biến trên khoảng $\left(-\frac{b}{2a};+\infty\right)$ ; |
| $-\frac{\Delta}{4a}$ là giá trị nhỏ nhất của hàm số.                   | $-\frac{\Delta}{4a}$ là giá trị lớn nhất của hàm số.                  |

**>> Vận dụng 2.** Bạn Nam đứng dưới chân cầu vượt ba tầng ở nút giao ngã ba Huế, thuộc thành phố Đà Nẵng để ngắm cầu vượt (H.6.13). Biết rằng trụ tháp cầu có dạng đường parabol, khoảng cách giữa hai chân trụ tháp khoảng 27 m, chiều cao của trụ tháp tính từ điểm trên

mặt đất cách chân trụ tháp 2,26 m là 20 m. Hãy giúp bạn Nam ước lượng độ cao của đỉnh trụ tháp cầu (so với mặt đất).

## Hướng dẫn

Chọn hệ trục toạ độ Oxy sao cho một chân trụ tháp đặt tại gốc toa đô, chân còn lại đặt trên tia Ox. Khi đó trụ tháp là một phần của đồ thị hàm số dạng  $y = ax^2 + bx$ .

![](_page_15_Picture_17.jpeg)

Hình 6.13. Cầu vượt ba tầng ở nút giao ngã ba Huế thuộc thành phố Đà Nẵng

# **BÀI TẬP**

6.7. Vẽ các đường parabol sau:

a) 
$$y = x^2 - 3x + 2$$
;

b) 
$$y = -2x^2 + 2x + 3$$
;

c) 
$$v = x^2 + 2x + 1$$
:

d) 
$$y = -x^2 + x - 1$$
.

- 6.8. Từ các parabol đã vẽ ở Bài tập 6.7, hãy cho biết khoảng đồng biến và khoảng nghịch biến của mỗi hàm số bậc hai tương ứng.
- **6.9.** Xác định parabol  $y = ax^2 + bx + 1$ , trong mỗi trường hợp sau:
  - a) Đi qua hai điểm A(1; 0) và B(2; 4);
  - b) Đi qua điểm A(1; 0) và có trục đối xứng x = 1;
  - c) Có đỉnh I(1; 2);
  - d) Đi qua điểm A(-1; 6) và có tung độ đỉnh -0,25.
- **6.10.** Xác định parabol  $y = ax^2 + bx + c$ , biết rằng parabol đó đi qua điểm A(8; 0) và có đỉnh là I(6; -12).
- **6.11.** Gọi (P) là đồ thị hàm số bậc hai  $y = ax^2 + bx + c$ . Hấy xác định dấu của hệ số a và biệt thức  $\Delta$ , trong mỗi trường hợp sau:
  - a) (P) nằm hoàn toàn phía trên trục hoành;
  - b) (P) nằm hoàn toàn phía dưới trục hoành;
  - c) (P) cắt trục hoành tại hai điểm phân biệt và có đỉnh nằm phía dưới trục hoành;
  - d) (P) tiếp xúc với trục hoành và nằm phía trên trục hoành.
- 6.12. Hai bạn An và Bình trao đổi với nhau.

An nói: Tớ đọc ở một tài liệu thấy nói rằng cổng Trường Đại học Bách khoa Hà Nội (H.6.14) có dạng một parabol, khoảng cách giữa hai chân cổng là 8 m và chiều cao của cổng tính từ một điểm trên mặt đất cách chân cổng 0,5 m là 2,93 m. Từ đó tớ tính ra được chiều cao của cổng parabol đó là 12 m.

Sau một hồi suy nghĩ, Bình nói. Nếu dữ kiện như bạn nói, thì chiều cao của cổng parabol mà bạn tính ra ở trên là không chính xác.

Dựa vào thông tin mà An đọc được, em hãy tính chiều cao của cổng Trường Đại học Bách khoa Hà Nội để xem kết quả bạn An tính được có chính xác không nhé!

![](_page_16_Picture_22.jpeg)

Hình 6.14. Cổng parabol của trường Đại học Bách khoa Hà Nội

- 6.13. Bác Hùng dùng 40 m lưới thép gai rào thành một mảnh vườn hình chữ nhật để trồng rau.
  - a) Tính diện tích mảnh vườn hình chữ nhật rào được theo chiều rộng x (mét) của nó.
  - b) Tìm kích thước của mảnh vườn hình chữ nhật có diện tích lớn nhất mà bác Hùng có thể rào được.
- 6.14. Quỹ đạo của một vật được ném lên từ gốc O (được chọn là điểm ném) trong mặt phẳng toạ độ Oxy là một parabol có phương trình  $y = \frac{-3}{1000}x^2 + x$ , trong đó x (mét) là khoảng

cách theo phương ngang trên mặt đất từ vị trí của vật đến gốc O, y (mét) là đô cao của vật so với mặt đất (H.6.15).

- a) Tìm độ cao cực đại của vật trong quá trình bay.
- b) Tính khoảng cách từ điểm cham đất sau khi bay của vật đến gốc O. Khoảng cách này gọi là tầm xa của quỹ đạo.

![](_page_17_Figure_3.jpeg)

## Em có biết?

## Một số mô hình toán học sử dụng hàm số bắc hai

Hàm số bậc hai được sử dụng trong nhiều mô hình thực tế. Dưới đây ta xét một số mô hình đơn giản thường gặp.

- Phương trình chuyển động của ∨ật chuyển động thẳng biến đổi đều

$$y = x_0 + v_0 t + \frac{at^2}{2}$$

trong đó  $x_0$  là toạ độ ban đầu của vật,  $v_0$  là vận tốc ban đầu của vật và a là gia tốc của vật (a cùng dấu với  $v_0$  nếu vật chuyển động nhanh dần đều và ngược dấu với  $v_0$  nếu vật chuyển động chậm dần đều). Như vậy toạ độ x(t) của vật là một hàm số bậc hai của thời gian t.

Nói riêng, khi bỏ qua sức cản của không khí, nếu ném một vật lên trên theo phương thẳng đứng thì chuyển động của vật sẽ chỉ chịu ảnh hưởng của trọng lực ∨à vật sẽ có gia tốc bằng gia tốc trọng trường. Khi đó độ cao (so với mặt đất) của vật tại thời điểm t cho bởi phương trình

$$y(t) = y_0 + v_0 t - \frac{1}{2}gt^2,$$

trong đó  $y_0$  (mét) là độ cao ban đầu của vật khi ném lên,  $v_0$ (m/s) là vận tốc ban đầu của vật và glà gia tốc trọng trường ( $g \approx 9.8 \text{ m/s}^2$ ).

Đặc biệt, khi bỏ qua sức cản không khí, nếu một vật rơi tự do từ độ cao  $y_0$  (mét) so với mặt đất thì độ cao y (mét) của nó tại thời điểm t (giây) cho bởi công thức

$$y(t)=h_0-\frac{1}{2}gt^2.$$

 $y(t) = h_0 - \frac{1}{2}gt^2$ . – Phương trình chuyển động của vật ném xiên

Một vật được ném từ độ cao h (mét) so với mặt đất, với vận tốc ban đầu  $v_0$  (m/s) hợp với phương ngang một góc  $\alpha$ . Khi đó quỹ đạo chuyển động của vật tuần theo phương trình

$$y = \frac{-g}{2v_0^2 \cos^2 \alpha} x^2 + x \tan \alpha + h,$$

ở đó x (mét) là khoảng cách ∨ật bay được theo phương ngang tính từ mặt đất tại điểm ném, y (mét) là độ cao so với mặt đất của vật trong quá trình bay, g là gia tốc trọng trường. Như vậy quỹ đạo chuyển động của một vật ném xiên là một parabol.

Tương tự, đường đi của quả bóng khi được cầu thủ đá lên không trung, quỹ đạo của ∨iên đạn pháo khi bắn ra khỏi nòng pháo, tia lửa hàn, hạt nước bắn lên từ đài phun nước,... đều có dạng đường parabol (H.6.16).

![](_page_18_Picture_1.jpeg)

![](_page_18_Picture_2.jpeg)

![](_page_18_Picture_3.jpeg)

Cầu thủ sút quả bóng

Đài phun nước ở Hồ Gươm

Tia lửa hàn

Hình 6.16

### - Doanh thu bán hàng

Trong kinh tế, doanh thu bán hàng là số tiền nhận được khi bán một mặt hàng. Doanh thu R bằng đơn giá x của mặt hàng (tức là giá bán của một sản phẩm) nhân với số lượng n sản phẩm đã bán được, tức là

$$R = x \cdot n$$
.

Định luật nhu cầu khẳng định rằng giữa x và n có mối liên hệ với nhau: Khi cái này tăng thì cái kia sẽ giảm. Phương trình liên hệ giữa x và n gọi là phương trình nhu cầu. Nếu phương trình nhu cầu là liên hệ bậc nhất, tức là n = a - bx (a, b là những hằng số dương) thì doanh thu bán hàng sẽ là hàm số bậc hai của đơn giá

$$R(x) = xn = x(a - bx) = ax - bx^{2}.$$

Khi đó người ta thường quan tâm đến việc tìm giá bán x để doanh thu đạt cực đại, hoặc tìm giá bán x để doanh thu vượt một mức nào đó.

# KẾT NỐI TRI THỰC VỚI CUỘC SỐNG

# DẤU CỦA TAM THỰC BẬC HAI

## THUẬT NGỮ

- Tam thức bậc hai
- Dấu của tam thức bâc hai
- Bất phương trình bâc hai

# KIẾN THỰC, KĨ NĂNG

- Giải thích Định lí về dấu của tam thức bậc hai từ việc quan sát đồ thị của hàm bậc hai.
- Giải bất phương trình bậc hai.
- Vân dung bất phương trình bậc hai vào giải quyết bài toán thực tiễn.

Xét bài toán rào vườn ở Bài 16, nhưng ta trả lời câu hỏi: Hai cột góc hàng rào (H.6.8) cần phải cắm cách bờ tường bao nhiều mét để mảnh đất được rào chắn có diện tích không nhỏ hon 48 m<sup>2</sup>?

# 1. DẦU CỦA TAM THỨC BẬC HAI

>> HD1. Hãy chỉ ra một đặc điểm chung của các biểu thức dưới đây:

$$A = 0.5x^2$$
;

$$B = 1 - x^2$$
:

$$C = x^2 + x + 1$$

$$C = x^2 + x + 1;$$
  $D = (1-x)(2x + 1).$ 

Tam thức bậc hai (đối với x) là biểu thức có dạng  $ax^2 + bx + c$ , trong đó a, b, c là những số thực cho trước (với  $a \neq 0$ ), được gọi là các hệ số của tam thức bậc hai.

Người ta thường viết  $f(x) = ax^2 + bx + c$ . Các đa thức đã cho trong HĐ1 là những tam thức bâc hai. Ở đa thức A, ta có a = 0.5; b = 0; c = 0.

**Duyện tập 1.** Hãy cho biết biểu thức nào sau đây là tam thức bậc hai.

$$A = 3x + 2\sqrt{x} + 1$$
;  $B = -5x^4 + 3x^2 + 4$ ;  $C = -\frac{2}{3}x^2 + 7x - 4$ ;  $D = \left(\frac{1}{x}\right)^2 + 2\frac{1}{x} + 3$ .

## Chú ý

Nghiệm của phương trình bậc hai  $ax^2 + bx + c = 0$ cũng được gọi là nghiệm của tam thức bậc hai  $ax^2 + bx + c$ .

 $\Delta = b^2 - 4ac$  và  $\Delta' = b^2 - ac$ , với b = 2b' tương ứng được gọi là biệt thức và biệt thức thu gọn của tam thức bậc hai  $ax^2 + bx + c$ .

- $\mathbb{R}$  HD2. Cho hàm số bậc hai  $y = f(x) = x^2 4x + 3$ .
  - a) Xác định hệ số a. Tính f(0), f(1), f(2), f(3), f(4) và nhận xét về dấu của chúng so với dấu của hệ số a.

![](_page_19_Picture_26.jpeg)

b) Cho đồ thị hàm số y = f(x) (H.6.17). Xét trên từng khoảng  $(-\infty; 1)$ , (1; 3),  $(3; +\infty)$ , đồ thị nằm phía trên hay nằm phía dưới truc Ox?

![](_page_20_Figure_1.jpeg)

![](_page_20_Figure_2.jpeg)

Hình 6.17

- **19 HD3.** Cho đồ thị hàm số  $y = g(x) = -2x^2 + x + 3$  như Hình 6.18.
  - a) Xét trên từng khoảng  $(-\infty; -1)$ ,  $\left(-1; \frac{3}{2}\right)$ ,  $\left(\frac{3}{2}; +\infty\right)$ , đồ thị nằm phía trên trục Ox hay nằm phía dưới trục Ox?
  - b) Nhận xét về dấu của g(x) và dấu của hệ số a trên từng khoảng đó.

![](_page_20_Figure_7.jpeg)

Hình 6.18

## Nhận xét

Từ HĐ2 và HĐ3 ta thấy, nếu tam thức bậc hai  $f(x) = ax^2 + bx + c$  có hai nghiệm phân biệt  $x_1$ ,  $x_2$  ( $x_1 < x_2$ ) thì f(x) luôn cùng dấu với hệ số a với mọi giá trị  $x \in (-\infty; x_1) \cup (x_2; +\infty)$  (ở ngoài đoạn hai nghiệm) và trái dấu với a với mọi giá trị  $x \in (x_1; x_2)$  (ở trong khoảng hai nghiệm).

- 🥦 ню4. Nêu nội dung thay vào ô có dấu "?" trong bảng sau cho thích hợp.
  - Trường hợp a > 0

| Δ                                   | Δ < 0                                      | Δ=0                                                   | $\Delta > 0$                                                                                                       |
|-------------------------------------|--------------------------------------------|-------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| Dạng đồ thị                         |                                            | $\frac{y}{O}$ $\frac{b}{-\frac{b}{2a}}$ $\frac{x}{x}$ | y x <sub>1</sub> x <sub>2</sub> x                                                                                  |
| Vị trí của đồ thị<br>so với trục Ox | Đồ thị nằm hoàn toàn<br>phía trên trục Ox. |                                                       | - Đồ thị nằm phía trên trục $Ox$ khi $x < x_1$ hoặc $x > x_2$ Đồ thị nằm phía dưới trục $Ox$ khi $x_1 < x < x_2$ . |

## • Trường hợp a < 0

![](_page_21_Figure_1.jpeg)

Mối quan hệ giữa dấu của tam thức bậc hai  $ax^2 + bx + c$  với dấu của hệ số a trong từng trường hợp của  $\Delta$  được phát biểu trong Định lí về dấu tam thức bậc hai sau đây.

Cho tam thức bậc hai  $f(x) = ax^2 + bx + c$  ( $a \ne 0$ ).

- Nếu ∆ < 0 thì f(x) cùng dấu với hệ số a với mọi x ∈ ℝ.</li>
- Nếu  $\Delta = 0$  thì f(x) cùng dấu với hệ số a với mọi  $x \neq -\frac{b}{2a}$  và  $f\left(-\frac{b}{2a}\right) = 0$ .
- Nếu ∆ > 0 thì tam thức f(x) có hai nghiệm phân biệt x<sub>1</sub> và x<sub>2</sub> (x<sub>1</sub> < x<sub>2</sub>). Khi đó, f(x) cùng dấu với hệ số a với mọi x ∈ (-∞; x<sub>1</sub>) ∪ (x<sub>2</sub>; +∞); f(x) trái dấu với hệ số a với mọi x ∈ (x<sub>1</sub>; x<sub>2</sub>).

Khi  $\Delta > 0$ , dấu của f(x) và a là: "Trong trái, ngoài cùng".

![](_page_21_Picture_9.jpeg)

Chú ý. Trong Định lí về dấu tam thức bậc hai có thể thay  $\Delta$  bởi  $\Delta$ '.

# **>>> Ví dụ 1.** Xét dấu các tam thức bậc hai sau:

a) 
$$x^2 + x + 1$$
;

b) 
$$-\frac{3}{2}x^2 + 9x - \frac{27}{2}$$
;

c) 
$$2x^2 + 6x - 8$$
.

Giài

a) 
$$f(x) = x^2 + x + 1$$
 có  $\Delta = -3 < 0$  và  $a = 1 > 0$  nên  $f(x) > 0$  với mọi  $x \in \mathbb{R}$ .

b) 
$$g(x) = -\frac{3}{2}x^2 + 9x - \frac{27}{2}$$
 có  $\Delta = 0$  và  $a = -\frac{3}{2} < 0$  nên  $g(x)$  có nghiệm kép  $x = 3$  và  $g(x) < 0$  với mọi  $x \neq 3$ .

c) Dễ thấy  $h(x) = 2x^2 + 6x - 8$  có  $\Delta' = 25 > 0$ , a = 2 > 0 và có hai nghiệm phân biệt  $x_1 = -4$ ;  $x_2 = 1$ . Do đó ta có bảng xét dấu h(x):

| Χ    | -00 |   | -4 |                | 1 |   | +∞ |
|------|-----|---|----|----------------|---|---|----|
| h(x) |     | + | 0  | 7 <u>850</u> 5 | 0 | + |    |

Suy ra h(x) > 0 với mọi  $x \in (-\infty, -4) \cup (1, +\infty)$  và h(x) < 0 với mọi  $x \in (-4, 1)$ .

Luyên tập 2. Xét dấu các tam thức bậc hai sau:

a) 
$$-3x^2 + x - \sqrt{2}$$
; b)  $x^2 + 8x + 16$ ;

b) 
$$x^2 + 8x + 16$$

c) 
$$-2x^2 + 7x - 3$$
.

# 2. BẤT PHƯƠNG TRÌNH BẬC HAI

汲 HĐ5. Trở lại *tình huống mở đầu*. Với yêu cầu mảnh đất được rào chắn có diện tích không nhỏ hơn 48 m<sup>2</sup>, hãy viết bất đẳng thức thể hiện sư so sánh biểu thức tính diện tích  $S(x) = -2x^2 + 20x \text{ v\'oi } 48.$ 

Từ HĐ5, ta có 
$$2x^2-20x+48 \le 0$$
. (1)

Đây là một bất phương trình bậc hai.

Tổng quát, ta có định nghĩa sau:

- Bất phương trình bậc hai ẩn x là bất phương trình có dạng  $ax^2 + bx + c > 0$  (hoặc  $ax^2 + bx + c \ge 0$ ,  $ax^2 + bx + c < 0$ ,  $ax^2 + bx + c \le 0$ ), trong đó a, b, c là những số thực đã cho và  $a \neq 0$ .
- Số thực x<sub>0</sub> gọi là một nghiệm của bất phương trình bậc hai ax² + bx + c > 0, nếu  $ax_0^2 + bx_0 + c > 0$ . Tập hợp gồm tất cả các nghiệm của bất phương trình bậc hai  $ax^2 + bx + c > 0$  gọi là *tập nghiệm* của bất phương trình này.
- Giải bất phương trình bậc hai  $f(x) = ax^2 + bx + c > 0$  là tìm tập nghiệm của nó, tức là tìm các khoảng mà trong đó f(x) cùng dấu với hệ số a (nếu a > 0) hay trái dấu với hệ số a (nếu a < 0).

Nhận xét. Để giải bất phương trình bậc hai  $ax^2 + bx + c > 0$  (hoặc  $ax^2 + bx + c \ge 0$ ,  $ax^2 + bx + c < 0$ ,  $ax^2 + bx + c \le 0$ ) ta cần xét dấu tam thức  $ax^2 + bx + c$ , từ đó suy ra tập nghiệm.

**>>> Ví dụ 2.** Giải các bất phương trình sau:

a) 
$$3x^2 + x + 5 \le 0$$

a) 
$$3x^2 + x + 5 \le 0$$
; b)  $-3x^2 + 2\sqrt{3}x - 1 \ge 0$ ; c)  $-x^2 + 2x + 1 > 0$ .

c) 
$$-x^2 + 2x + 1 > 0$$
.

Giai

- a) Tam thức  $f(x) = 3x^2 + x + 5$  có  $\Delta = -59 < 0$ , hệ số a = 3 > 0 nên f(x) luôn dương (cùng dấu với a) với mọi x, tức là  $3x^2 + 5x + 5 > 0$  với mọi  $x \in \mathbb{R}$ . Suy ra bất phương trình vô nghiệm.
- b) Tam thức  $f(x) = -3x^2 + 2\sqrt{3}x 1$  có  $\Delta' = 0$ , hệ số a = -3 < 0 nên f(x) luôn âm (cùng dấu với a) với mọi  $x \neq \frac{\sqrt{3}}{3}$ , tức là  $-3x^2 + 2\sqrt{3}x - 1 < 0$  với mọi  $x \neq \frac{\sqrt{3}}{3}$ .

Suy ra bất phương trình có nghiệm duy nhất  $x = \frac{\sqrt{3}}{3}$ .

c) Tam thức  $f(x) = -x^2 + 2x + 1$  có  $\Delta' = 2 > 0$  nên f(x) có hai nghiệm  $x_1 = 1 - \sqrt{2}$  và  $x_2 = 1 + \sqrt{2}$ .

Mặt khác a = -1 < 0, do đó ta có bảng xét dấu sau:

| Х    | -∞ |   | 1– √2 |   | 1+ √2 |            | +∞ |
|------|----|---|-------|---|-------|------------|----|
| f(x) |    | - | 0     | + | 0     | 1 <u>—</u> |    |

Tập nghiệm của bất phương trình là  $S = (1 - \sqrt{2}; 1 + \sqrt{2}).$ 

Didu 3. Giải bất phương trình (1), từ đó suy ra lời giải cho bài toán rào vườn ở *tình huống* mở đầu.

## Giải

Tam thức bậc hai  $f(x) = 2x^2 - 20x + 48$  có hai nghiệm  $x_1 = 4$ ;  $x_2 = 6$  và hệ số a = 2 > 0. Từ đó suy ra tập nghiệm của bất phương trình (1) là đoạn [4; 6]. Như vậy khoảng cách từ điểm cắm cột đến bờ tường phải lớn hơn hoặc bằng 4 m và nhỏ hơn hoặc bằng 6 m thì mảnh đất rào chắn của bác Việt sẽ có diện tích không nhỏ hơn 48 m<sup>2</sup>.

Luyện tập 3. Giải các bất phương trình bậc hai sau:

a) 
$$-5x^2 + x - 1 \le 0$$
:

b) 
$$x^2 - 8x + 16 \le 0$$
; c)  $x^2 - x + 6 > 0$ .

c) 
$$x^2 - x + 6 > 0$$

>> Vân dụng. Độ cao so với mặt đất của một quả bóng được ném lên theo phương thẳng đứng được mô tả bởi hàm số bậc hai  $h(t) = -4.9t^2 + 20t + 1$ , ở đó độ cao h(t) tính bằng mét và thời gian t tính bằng giây. Trong khoảng thời điểm nào trong quá trình bay của nó, quả bóng sẽ ở độ cao trên 5 m so với mặt đất?

## Tìm hiểu thêm

Ta có thể dùng máy tính cầm tay để giải bất phương trình bậc hai. Sau khi mở máy, ta bấm liên tiếp các phím sau đây:

| Mode | <b>\</b> | 1 | 1 |
|------|----------|---|---|
|      | 1        |   |   |

Sau đó chọn một trong bốn dạng bất phương trình bậc hai rồi nhập các hệ số a, b, c, từ đó nhân được nghiệm.

Ví dụ để giải bất phương trình:  $2x^2 - 3x - 6 \le 0$  ta bấm tổ hợp phím

Màn hình máy tính hiển thị:  $\frac{3-\sqrt{57}}{4} \le x \le \frac{3+\sqrt{57}}{4}$ .

Tập nghiệm của bất phương trình là  $\begin{bmatrix} 3-\sqrt{57} \\ 4 \end{bmatrix}$ ,  $\frac{3-\sqrt{57}}{4} \le \chi \le \frac{3+\sqrt{57}}{4}$ 

# **BÀI TẬP**

6.15. Xét dấu các tam thức bậc hai sau:

a) 
$$3x^2 - 4x + 1$$
;

b) 
$$x^2 + 2x + 1$$
;

c) 
$$-x^2 + 3x - 2$$
;

d) 
$$-x^2 + x - 1$$
.

6.16. Giải các bất phương trình bậc hai:

a) 
$$x^2 - 1 \ge 0$$
;

b) 
$$x^2 - 2x - 1 < 0$$
;

c) 
$$-3x^2 + 12x + 1 \le 0$$
;

d) 
$$5x^2 + x + 1 \ge 0$$
.

**6.17.** Tìm các giá trị của tham số m để tam thức bậc hai sau dương với mọi  $x \in \mathbb{R}$ :

$$x^2 + (m + 1)x + 2m + 3$$
.

- **6.18.** Một vật được ném theo phương thẳng đứng xuống dưới từ độ cao 320 m với vận tốc ban đầu  $v_{\rm Q}=20$  m/s. Hỏi sau ít nhất bao nhiêu giây, vật đó cách mặt đất không quá 100 m? Giả thiết rằng sức cản của không khí là không đáng kể.
- 6.19. Xét đường tròn đường kính AB = 4 và một điểm M di chuyển trên đoạn AB, đặt AM = x (H.6.19). Xét hai đường tròn đường kính AM và MB. Kí hiệu S(x) là diện tích phần hình phẳng nằm trong hình tròn lớn và nằm ngoài hai hình tròn nhỏ. Xác định các giá trị của x để diện tích S(x) không vượt quá một nửa tổng diện tích hai hình tròn nhỏ.

![](_page_24_Picture_15.jpeg)

Hình 6.19

KẾT NỐI TRI THỰC VỚI CUỘC SỐNG

# PHƯƠNG TRÌNH QUY VỀ PHƯƠNG TRÌNH BÁC HAI

# THUẬT NGỮ

Phương trình chứa căn thức

# KIẾN THỨC, KĨ NĂNG

Giải một số phương trình chứa căn bậc hai đơn giản có thể quy về phương trình bậc hai.

Trong bài này chúng ta sẽ giải các phương trình chứa căn thức thường gặp có dạng  $\sqrt{ax^2 + bx + c} = \sqrt{dx^2 + ex + f}$  và  $\sqrt{ax^2 + bx + c} = dx + e$ .

**1. PHUONG TRÌNH DẠNG** 
$$\sqrt{ax^2 + bx + c} = \sqrt{dx^2 + ex + f}$$

- **19 HD1.** Cho phương trình  $\sqrt{x^2 3x + 2} = \sqrt{-x^2 2x + 2}$ .
  - a) Bình phương hai vế phương trình để khử căn và giải phương trình bậc hai nhận được.
  - b) Thử lại các giá trị x tìm được ở câu a có thoả mãn phương trình đã cho hay không.

Để giải phương trình  $\sqrt{ax^2 + bx + c} = \sqrt{dx^2 + ex + f}$ , ta thực hiện như sau:

- Bình phương hai vế và giải phương trình nhận được;
- Thử lại các giá trị x tìm được ở trên có thoả mãn phương trình đã cho hay không và kết luận nghiệm.

**Ví dụ 1.** Giải phương trình 
$$\sqrt{2x^2 - 4x - 2} = \sqrt{x^2 - x - 2}$$

Giải

Bình phương hai vế của phương trình, ta được

$$2x^2 - 4x - 2 = x^2 - x - 2$$
.

Sau khi thu gọn ta được  $x^2 - 3x = 0$ . Từ đó x = 0 hoặc x = 3.

Thay lần lượt hai giá trị này của x vào phương trình đã cho, ta thấy chỉ có x = 3 thoả mãn. Vây nghiệm của phương trình đã cho là x = 3.

**>>> Luyện tập 1.** Giải các phương trình sau:

a) 
$$\sqrt{3x^2-6x+1} = \sqrt{-2x^2-9x+1}$$
;

b) 
$$\sqrt{2x^2 - 3x - 5} = \sqrt{x^2 - 7}$$
.

# **2. PHUONG TRÌNH DANG** $\sqrt{ax^2 + bx + c} = dx + e$ .

- **10. HD2.** Cho phương trình  $\sqrt{26x^2 63x + 38} = 5x 6$ .
  - a) Bình phương hai vế và giải phương trình nhận được.
  - b) Thử lại các giá trị x tìm được ở câu a có thoả mãn phương trình đã cho hay không.

Để giải phương trình  $\sqrt{ax^2 + bx + c} = dx + e$ , ta thực hiện như sau:

- Bình phương hai vế và giải phương trình nhận được;
- Thử lại các giá trị x tìm được ở trên có thoả mãn phương trình đã cho hay không và kết luận nghiệm.
- **)** Ví dụ 2. Giải phương trình  $\sqrt{2x^2 5x 9} = x 1$ .

## Giải

Bình phương hai vế của phương trình ta được

$$2x^2 - 5x - 9 = x^2 - 2x + 1$$
.

Sau khi thu gọn ta được  $x^2 - 3x - 10 = 0$ . Từ đó x = -2 hoặc x = 5.

Thay lần lượt hai giá trị này của x vào phương trình đã cho, ta thấy chỉ có x = 5 thoả mãn.

Vậy nghiệm của phương trình đã cho là x = 5.

Với x = -2 thì vế phải âm, vế trái không âm. Do đó, ta có thể kết luận x = -2 không là nghiệm của phương trình đã cho mà không cần thử lại.

![](_page_26_Picture_11.jpeg)

Luyện tập 2. Giải các phương trình sau:

a) 
$$\sqrt{2x^2 + x + 3} = 1 - x$$
;

b) 
$$\sqrt{3x^2 - 13x + 14} = x - 3$$
.

Vận dụng. Bác Việt sống và làm việc tại trạm hải đăng cách bờ biển 4 km. Hằng tuần bác chèo thuyền vào vị trí gần nhất trên bờ biển là bến Bính để nhận hàng hoá do cơ quan cung cấp. Tuần này, do trục trặc về vận chuyển nên toàn bộ số hàng vẫn đang nằm ở thôn Hoành, bên bờ biển cách bến Bính 9,25 km và sẽ được anh Nam vận chuyển trên con đường dọc bờ biển tới bến Bính bằng xe kéo. Bác Việt đã gọi điện thống nhất với anh Nam là họ sẽ gặp nhau ở vị trí nào đó giữa bến Bính và thôn Hoành để hai người có mặt tại đó cùng lúc, không mất thời gian chờ nhau. Tìm vị trí hai người dự định gặp nhau, biết rằng vận tốc kéo xe của anh Nam là 5 km/h và thuyền của bác Việt di chuyển với vận tốc 4 km/h. Ngoài ra giả thiết rằng đường bờ biển từ thôn Hoành đến bến Bính là đường thẳng và bác Việt cũng luôn chèo thuyền tới một điểm trên bờ biển theo một đường thẳng.

# Hướng dẫn

Ta mô hình hoá bài toán như trong Hình 6.20: Trạm hải đăng ở vị trí A; bến Bính ở B và thôn Hoành ở C. Giả sử bác Việt chèo thuyền cập bến ở vị trí M và ta đặt BM = x (x > 0). Để hai người không phải chờ nhau thì thời gian chèo thuyền bằng thời gian kéo xe nên ta có phương trình:

![](_page_26_Figure_18.jpeg)

$$\frac{\sqrt{x^2+16}}{4} = \frac{9,25-x}{5}.$$

Giải phương trình này sẽ tìm được vị trí hai người dự định gặp nhau.

# **BÀI TÂP**

6.20. Giải các phương trình sau:

a) 
$$\sqrt{3x^2 - 4x - 1} = \sqrt{2x^2 - 4x + 3}$$
; b)  $\sqrt{x^2 + 2x - 3} = \sqrt{-2x^2 + 5}$ ;

c) 
$$\sqrt{2x^2 + 3x - 3} = \sqrt{-x^2 - x + 1}$$
:

a) 
$$\sqrt{6x^2 + 13x + 13} = 2x + 4$$
;

c) 
$$\sqrt{3x^2 - 17x + 23} = x - 3$$
;

b) 
$$\sqrt{x^2 + 2x - 3} = \sqrt{-2x^2 + 5}$$
;

d) 
$$\sqrt{-x^2+5x-4} = \sqrt{-2x^2+4x+2}$$
.

b) 
$$\sqrt{2x^2 + 5x + 3} = -3 - x$$
;

d) 
$$\sqrt{-x^2+2x+4} = x-2$$
.

6.22. Cho tứ giác ABCD có  $AB \perp CD$ ; AB = 2; BC = 13; CD = 8; DA = 5 (H.6.21). Gọi Hlà giao điểm của AB và CD và đặt x = AH. Hãy thiết lập một phương trình để tính độ dài x, từ đó tính diện tích tứ giác ABCD.

![](_page_27_Figure_12.jpeg)

Hình 6.21

6.23. Hằng ngày bạn Hùng đều đón bạn Minh đi học tại một vị trí trên lề đường thẳng đến trường. Minh đứng tại vị trí A cách lễ đường một khoảng 50 m để chờ Hùng. Khi nhìn thấy Hùng đạp xe đến địa điểm B, cách mình một đoạn 200 m thì Minh bắt đầu đi bộ ra lề đường để bắt kịp xe. Vận tốc đi bộ của Minh là 5 km/h, vận tốc xe đạp của Hùng là 15 km/h. Hãy xác định vị trí C trên lề đường (H.6.22) để hai bạn gặp nhau mà không bạn nào phải chờ người kia (làm tròn kết quả đến hàng phần mười).

![](_page_27_Picture_15.jpeg)

# BÀI TẬP CUỐI CHƯƠNG VI

# A - TRẮC NGHIỆM

Chon phương án đúng.

6.24. Tập xác định của hàm số  $y = \frac{1}{\sqrt{x-2}}$  là

**A.** 
$$D = [2; +\infty)$$
.

**B.** 
$$D = (2; +\infty)$$
.

C. 
$$D = \mathbb{R} \setminus \{2\}$$
.

D. 
$$D = \mathbb{R}$$
.

**6.25.** Parabol  $y = -x^2 + 2x + 3$  có đỉnh là

**A.** 
$$I(-1; 0)$$
.

**6.26.** Hàm số  $v = x^2 - 5x + 4$ 

A. Đồng biến trên khoảng  $(1:+\infty)$ .

**B.** Đồng biến trên khoảng  $(-\infty; 4)$ .

C. Nghịch biến trên khoảng  $(-\infty; 1)$ .

D. Nghịch biến trên khoảng (1; 4).

**6.27.** Bất phương trình  $x^2 - 2mx + 4 > 0$  nghiệm đúng với mọi  $x \in \mathbb{R}$  khi

**A.** 
$$m = -1$$
.

**B.** 
$$m = -2$$
.

C. 
$$m = 2$$
.

**D.** 
$$m > 2$$
.

6.28. Tập nghiệm của phương trình  $\sqrt{2x^2 - 3} = x - 1$  là

**A.** 
$$\{-1-\sqrt{5};-1+\sqrt{5}\}.$$
 **B.**  $\{-1-\sqrt{5}\}.$  **C.**  $\{-1+\sqrt{5}\}.$ 

**B.** 
$$\{-1-\sqrt{5}\}$$

C. 
$$\{-1+\sqrt{5}\}$$
.

B - TỰ LUẬN

**6.29.** Tìm tập xác định của các hàm số sau: a)  $y = \sqrt{2x-1} + \sqrt{5-x}$ ; b)  $y = \frac{1}{\sqrt{x-1}}$ .

a) 
$$y = \sqrt{2x-1} + \sqrt{5-x}$$

b) 
$$y = \frac{1}{\sqrt{x-1}}$$
.

6.30. Với mỗi hàm số dưới đây, hãy vẽ đồ thị, tìm tập giá trị, khoảng đồng biến, khoảng nghịch biến của nó:

a) 
$$y = -x^2 + 6x - 9$$
;

b) 
$$y = -x^2 - 4x + 1$$
;

c) 
$$y = x^2 + 4x$$
;

d) 
$$y = 2x^2 + 2x + 1$$
.

**6.31.** Xác định parabol (P):  $y = ax^2 + bx + 3$  trong mỗi trường hợp sau:

a) (P) đi qua hai điểm A(1; 1) và B(-1; 0);

b) (P) đi qua điểm M(1; 2) và nhận đường thẳng x = 1 làm trục đối xứng;

c) (P) có đỉnh là I(1; 4).

6.32. Giải các bất phương trình sau:

a) 
$$2x^2 - 3x + 1 > 0$$
;

b) 
$$x^2 + 5x + 4 < 0$$
;

c) 
$$-3x^2 + 12x - 12 \ge 0$$
;

d) 
$$2x^2 + 2x + 1 < 0$$
.

6.33. Giải các phương trình sau:

a) 
$$\sqrt{2x^2-14} = x-1$$
;

b) 
$$\sqrt{-x^2-5x+2} = \sqrt{x^2-2x-3}$$
.

6.34. Một công ty bắt đầu sản xuất và bán một loại máy tính xách tay từ năm 2018. Số lượng loại máy tính đó bán được trong hai năm liên tiếp 2018 và 2019 lần lượt là 3,2 nghìn và 4 nghìn chiếc. Theo nghiên cứu dự báo thị trường của công ty, trong khoảng 10 năm kể từ năm 2018, số lượng máy tính loại đó bán được mỗi năm có thể được xấp xỉ bởi một hàm số bâc hai.

Giả sử t là thời gian (theo đơn vị năm) tính từ năm 2018. Số lượng loại máy tính đó bán được trong năm 2018 và năm 2019 lần lượt được biểu diễn bởi các điểm (0; 3,2) và (1; 4). Giả sử điểm (0; 3,2) là đỉnh đồ thị của hàm số bậc hai này.

- a) Lập công thức của hàm số mô tả số lượng máy tính xách tay bán được qua từng năm.
- b) Tính số lượng máy tính xách tay đó bán được trong năm 2024.
- c) Đến năm bao nhiều thì số lượng máy tính xách tay đó bán được trong năm sẽ vượt mức 52 nghìn chiếc?

# KẾT NỐI TRI THỰC VỚI CUỘC SỐNG

![](_page_30_Figure_0.jpeg)

Sau điểm và vectơ, những đối tượng khác của hình học phẳng như đường thẳng, đường tròn, ... sẽ lần lượt được đại số hoá ở chương này. Đối với mỗi đối tượng hình học đó, trước hết ta đưa ra đối tượng đại số tương ứng, được gọi là phương trình của nó. Các mối quan hệ, công thức tính toán hình học sẽ được thể hiện theo các yếu tố của phương trình tương ứng.

Nhờ đại số hoá hình học, ta có thể dùng ngôn ngữ và phương pháp của đại số để diễn đạt và học tập hình học. Ngoài ra, đại số hoá hình học là bước quan trọng cho phép ta dùng ngôn ngữ của máy tính để diễn đạt hình học. Nhờ đó, ta có thể sử dụng công nghệ thông tin trong học tập và áp dụng hình học, chẳng hạn, các phần mềm vẽ hình như GeoGebra (dùng trong học tập), Autocad (dùng trong vẽ thiết kế) đều sử dụng các kiến thức hình học.

Bài 19

# PHƯƠNG TRÌNH ĐƯỜNG THẮNG

## THUẬT NGỮ

- Vector chi phurong
- Vecto pháp tuyến
- · Phương trình tổng quát
- Phương trình tham số

# KIẾN THỰC, KĨ NĂNG

- Mô tả phương trình tổng quát và phương trình tham số của đường thẳng.
- Lập phương trình của đường thẳng khi biết một điểm và một vector pháp tuyến hoặc một điểm và một vector chỉ phương hoặc hai điểm.
- Giải thích mối liên hệ giữa đồ thị hàm bậc nhất và đường thẳng.
- Vận dụng kiến thức về phương trình đường thẳng để giải một số bài toán có liên quan đến thực tiễn.

Đường thẳng là một tập hợp điểm, được xác định bởi tính chất đặc trưng của các điểm thuộc đường thẳng đó. Do vậy, ta có thể đại số hoá đường thẳng bằng cách thể hiện tính chất đặc trưng đó bởi điều kiện đại số đối với toạ độ của các điểm tương ứng.

# 1. PHƯƠNG TRÌNH TỔNG QUÁT CỦA ĐƯỜNG THẮNG

**M** sao cho  $\overrightarrow{AM}$  vuông góc với  $\overrightarrow{n}$ .

![](_page_31_Picture_2.jpeg)

Hình 7.1a

Vector  $\vec{n}$  khác  $\vec{0}$  được gọi là vector pháp tuyến của đường thẳng  $\Delta$  nếu giá của nó vuông góc với  $\Delta$ .

![](_page_31_Figure_5.jpeg)

## Hình 7.1b

## Nhận xét

- Nếu  $\vec{n}$  là vectơ pháp tuyến của đường thẳng  $\Delta$  thì  $k\vec{n}$  ( $k \neq 0$ ) cũng là vectơ pháp tuyến của  $\Delta$ .
- Đường thẳng hoàn toàn xác định nếu biết một điểm và một vecto pháp tuyến của nó.
- Ví dụ 1. Trong mặt phẳng toạ độ, cho tam giác có ba đỉnh là A(3; 1), B(4; 0), C(5; 3). Hãy chỉ ra một vectơ pháp tuyến của đường trung trực của đoạn thẳng AB và một vectơ pháp tuyến của đường cao kẻ từ A của tam giác ABC.

#### Giải

Đường trung trực của đoạn thẳng AB vuông góc với AB nên có vectơ pháp tuyến  $\overrightarrow{AB}$ (1; – 1). Đường cao kẻ từ A của tam giác ABC vuông góc với BC nên có vectơ pháp tuyến  $\overrightarrow{BC}$ (1; 3).

**H92.** Trong mặt phẳng toạ độ, cho đường thẳng  $\Delta$  đi qua điểm  $A(x_0; y_0)$  và có vectơ pháp tuyến n(a; b). Chứng minh rằng điểm M(x; y) thuộc  $\Delta$  khi và chỉ khi

$$a(x - x_0) + b(y - y_0) = 0. (1)$$

## Nhận xét

Trong HĐ2, nếu đặt  $c = -ax_0 - by_0$  thì (1) còn được viết dưới dạng ax + by + c = 0 và được gọi là *phương trình tổng quát* của  $\Delta$ . Như vậy, điểm M(x; y) thuộc đường thẳng  $\Delta$  khi và chỉ khi toạ độ của nó thoả mãn phương trình tổng quát của  $\Delta$ .

Trong mặt phẳng toạ độ, mọi đường thẳng đều có phương trình tổng quát dạng ax + by + c = 0, với a và b không đồng thời bằng 0. Ngược lại, mỗi phương trình dạng ax + by + c = 0, với a và b không đồng thời bằng 0, đều là phương trình của một đường thẳng, nhận  $\vec{n}(a; b)$  là một vectơ pháp tuyến.

**)** Ví dụ 2. Trong mặt phẳng toạ độ, lập phương trình tổng quát của đường thẳng  $\Delta$  đi qua điểm A(2; 1) và nhận  $\vec{n}(3; 4)$  là một vectơ pháp tuyến.

## Giải

Đường thẳng  $\Delta$  có phương trình là 3(x-2)+4(y-1)=0 hay 3x+4y-10=0.

- **Luyện tập 1.** Trong mặt phẳng toạ độ, cho tam giác có ba đỉnh A(-1; 5), B(2; 3), C(6; 1). Lập phương trình tổng quát của đường cao kẻ từ A của tam giác ABC.
- **)> Ví dụ 3.** Trong mặt phẳng toạ độ, lập phương trình đường thẳng  $\Delta$  đi qua điểm A(0; b) và có vecto pháp tuyến n(a; -1), với a, b là các số cho trước. Đường thẳng  $\Delta$  có mối liên hệ gì với đồ thị của hàm số y = ax + b.

## Giải

Đường thẳng  $\Delta$  có phương trình là a(x-0)-1(y-b)=0 hay ax-y+b=0.

Đường thẳng  $\Delta$  là tập hợp những điểm M(x; y) thoả mãn ax - y + b = 0 (hay là, y = ax + b).

Do đó, đồ thị của hàm số y = ax + b chính là đường thẳng  $\Delta$ : ax - y + b = 0.

**Luyện tập 2.** Hãy chỉ ra một vec tơ pháp tuyến của đường thẳng  $\Delta: y = 3x + 4$ .

Nhận xét. Trong mặt phẳng toạ độ, cho đường thẳng  $\Delta$ : ax + by + c = 0.

- Nếu b=0 thì phương trình  $\Delta$  có thể đưa về dạng x=m (với  $m=-\frac{c}{a}$ ) và  $\Delta$  vuông góc với Ox.
- Nếu  $b \neq 0$  thì phương trình  $\Delta$  có thể đưa về dạng y = nx + p (với  $n = -\frac{a}{b}, p = -\frac{c}{b}$ ).

## 2. PHƯƠNG TRÌNH THAM SỐ CỦA ĐƯỜNG THẮNG

>> HĐ3. Trong Hình 7.2a, nếu một vật thể chuyển động với vector vận tốc bằng  $\vec{v}$  và đi qua A thì nó di chuyển trên đường nào?

Vector  $\vec{u}$  khác  $\vec{0}$  được gọi là vector chỉ phương của đường thẳng  $\Delta$  nếu giá của nó song song hoặc trùng với  $\Delta$ .

![](_page_32_Picture_13.jpeg)

Hình 7.2a

## Nhận xét

- Nếu  $\vec{u}$  là vectơ chỉ phương của đường thẳng  $\Delta$  thì  $k\vec{u}$  ( $k \neq 0$ ) cũng là vectơ chỉ phương của  $\Delta$ .
- Đường thẳng hoàn toàn xác định nếu biết một điểm và một vectơ chỉ phương của nó.
- Hai vector n(a; b) và u(-b; a) vuông góc với nhau nên nếu n
  là vector pháp tuyến của đường thẳng ∆ thì u
  là vector chỉ
  phương của đường thẳng đó và ngược lại.

![](_page_32_Figure_19.jpeg)

Hình 7.2b

Ví dụ 4. Trong mặt phẳng toạ độ, cho A(3; 2), B(1; – 4). Hấy chỉ ra hai vectơ chỉ phương của đường thẳng AB.

#### Giải

Đường thẳng  $\overrightarrow{AB}$  nhận  $\overrightarrow{AB}(-2;-6)$  là một vectơ chỉ phương.

Lấy  $\vec{u} = -\frac{1}{2}\vec{AB} = (1; 3)$ , khi đó  $\vec{u}$  cũng là một vectơ chỉ phương của đường thẳng AB.

- **Luyện tập 3.** Hãy chỉ ra một vectơ chỉ phương của đường thẳng  $\Delta:2x-y+1=0$ .
- **)> HĐ4.** Chuyển động của một vật thể được thể hiện trên mặt phẳng Oxy. Vật thể khởi hành từ A(2; 1) và chuyển động thẳng đều với vectơ vận tốc là  $\vec{v}(3; 4)$ .
  - a) Hỏi vật thể chuyển động trên đường thẳng nào (chỉ ra điểm đi qua và vectơ chỉ phương của đường thẳng đó)?
  - b) Chứng minh rằng, tại thời điểm t (t > 0) tính từ khi khởi hành, vật thể ở vị trí có toạ độ là (2+3t;1+4t).

Cho đường thẳng  $\Delta$  đi qua điểm  $A(x_0; y_0)$  và có vectơ chỉ phương  $\vec{u}(a; b)$ . Khi đó điểm M(x; y) thuộc đường thẳng  $\Delta$  khi và chỉ khi tồn tại số thực t sao cho  $\overline{AM} = t\vec{u}$ , hay

$$\begin{cases} x = x_0 + at \\ y = y_0 + bt. \end{cases}$$
 (2)

Hệ (2) được gọi là phương trình tham số của đường thẳng  $\Delta$  (t là tham số).

**)** Ví dụ 5. Lập phương trình tham số của đường thẳng  $\Delta$  đi qua điểm A(2; -3) và có vectơ chỉ phương  $\vec{u}(4; -1)$ .

Giải

Phương trình tham số của đường thẳng  $\Delta$  là

$$\begin{cases} x = 2 + 4t \\ y = -3 - t. \end{cases}$$

- **Luyện tập 4.** Lập phương trình tham số của đường thẳng  $\Delta$  đi qua điểm M(-1; 2) và song song với đường thẳng d: 3x 4y 1 = 0.
- ) Ví dụ 6. Lập phương trình tham số của đường thẳng đi qua hai điểm A(2; 3) và B(1; 5). Giải

Đường thẳng AB đi qua A(2; 3) và có vectơ chỉ phương  $\overrightarrow{AB} = (-1; 2)$ , do đó có phương trình tham số là  $\begin{cases} x = 2 - t \\ y = 3 + 2t. \end{cases}$ 

**Luyện tập 5.** Lập phương trình tham số và phương trình tổng quát của đường thẳng đi qua hai điểm phân biệt  $A(x_1; y_1)$ ,  $B(x_2; y_2)$  cho trước.

Vận dụng. Việc quy đổi nhiệt độ giữa đơn vị độ C (Anders Celsius, 1 701 – 1 744) và đơn vị độ F (Daniel Fahrenheit, 1 686 – 1 736) được xác định bởi hai mốc sau:

Nước đóng băng ở 0°C, 32°F;

Nước sôi ở 100°C, 212°F.

Trong quy đổi đó, nếu a°C tương ứng với b°F thì trên mặt phẳng toạ độ Oxy, điểm M(a; b) thuộc đường thẳng đi qua A(0; 32) và B(100; 212).

Hỏi 0°F, 100°F tương ứng với bao nhiêu đô C?

![](_page_34_Figure_5.jpeg)

Nhiệt kế dùng hai đơn vị đo là độ F và độ C

# **BÀI TẬP**

- **7.1.** Trong mặt phẳng toạ độ, cho  $\vec{n} = (2; 1), \vec{v} = (3; 2), A(1; 3), B(-2; 1).$
- a) Lập phương trình tổng quát của đường thẳng  $\Delta_1$  đi qua A và có vectơ pháp tuyến  $\vec{n}$ .
- b) Lập phương trình tham số của đường thẳng  $\Delta_2$  đi qua B và có vectơ chỉ phương  $\vec{v}$ .
- c) Lập phương trình tham số của đường thẳng AB.
- 7.2. Lập phương trình tổng quát của các trục toạ độ.
- **7.3.** Cho hai đường thẳng  $\Delta_1 : \begin{cases} x = 1 + 2t \\ y = 3 + 5t. \end{cases}$  và  $\Delta_2 : 2x + 3y 5 = 0$ .
- a) Lập phương trình tổng quát của  $\Delta_1$ .
- b) Lập phương trình tham số của  $\Delta_2$ .
- 7.4. Trong mặt phẳng toạ độ, cho tam giác ABC có A(1; 2), B(3; 0) và C(-2; -1).
- a) Lập phương trình đường cao kẻ từ A.
- b) Lập phương trình đường trung tuyến kẻ từ B.
- 7.5. (Phương trình đoạn chắn của đường thẳng) Chứng minh rằng, đường thẳng đi qua hai điểm A(a; 0), B(0; b) với  $ab \neq 0$  (H.7.3) có phương trình là

$$\frac{x}{a} + \frac{y}{b} = 1$$
.

![](_page_34_Figure_21.jpeg)

**7.6.** Theo Google Maps, sân bay Nội Bài có vĩ độ 21,2° Bắc, kinh độ 105,8° Đông, sân bay Đà Nẵng có vĩ độ 16,1° Bắc, kinh độ 108,2° Đông. Một máy bay, bay từ Nội Bài đến sân bay Đà Nẵng. Tại thời điểm t giờ, tính từ lúc xuất phát, máy bay ở vị trí có vĩ độ x° Bắc, kinh độ y° Đông được tính theo công thức

$$\begin{cases} x = 21, 2 - \frac{153}{40}t \\ y = 105, 8 + \frac{9}{5}t. \end{cases}$$

- a) Hỏi chuyến bay từ Hà Nội đến Đà Nẵng mất mấy giờ?
- b) Tại thời điểm 1 giờ kể từ lúc cất cánh, máy bay đã bay qua vĩ tuyến 17 (17º Bắc) chưa?

## Em có biết?

Hồi quy tuyến tính là một phương pháp được sử dụng trong thống kê để dự báo về mối quan hệ giữa các đại lượng dựa trên kết quả thống kê mẫu. Chẳng hạn, để dự báo về mối quan hệ giữa hai đại lượng x và y (y phụ thuộc vào x như thế nào), từ kết quả thống kê được thể hiện ở Hình 7.4a, phương pháp hồi quy tuyến tính đưa ra đường thẳng  $\Delta$  (H.7.4b) thể hiện gần đúng nhất mối quan hệ giữa các đại lượng x và y đã được thống kê. Về mặt hình ảnh, các chấm xanh trên hình vẽ (có toạ độ là các cặp giá trị (x; y) trong kết quả thống kê, tập trung dọc theo  $\Delta$ .

Để xác định  $\Delta$  (phương trình y=ax+b), người ta thường dùng tiêu chuẩn gọi là bình phương nhỏ nhất như sau: Với mỗi cặp  $(x_0; y_0)$  trong kết quả thống kê, xét bình phương khoảng cách từ  $M(x_0; y_0)$  đến  $M'(x_0; ax_0+b)$ . Khi đó, a, b được chọn sao cho tổng các bình phương này là nhỏ nhất.

Nhờ đưa ra được đường thẳng biểu thị (gần đúng) sự phụ thuộc giữa đại lượng y theo đại lượng x, người ta có thể đưa ra các dự báo nằm ngoài kết quả thống kê. Tất nhiên, không phải mô hình nào cũng phù hợp với phương pháp này, ngay cả khi kết quả thống kê tập trung dọc một đường thẳng. Chẳng hạn, để xác định đường đi của một quả tên lửa, nếu dựa vào một số quan sát ban đầu để dự đoán, ta có thể nghĩ rằng nó chuyển động thẳng, nhưng trên thực tế, nhìn chung nó đi theo đường parabol. Sai lầm trong những dự báo như vậy thật là tai hại!

![](_page_35_Figure_7.jpeg)

![](_page_35_Figure_8.jpeg)

Hình 7.4

# VỊ TRÍ TƯƠNG ĐỐI GIỮA HAI ĐƯỜNG THẮNG. GÓC VÀ KHOẢNG CÁCH

## THUẬT NGỮ

- · Góc, khoảng cách
- Vị trí tương đối giữa hai đường thẳng

# KIẾN THỨC, KĨ NĂNG

- Nhận biết hai đường thẳng cắt nhau, song song, trùng nhau, vuông góc.
- Thiết lập công thức tính góc giữa hai đường thẳng.
- Tính khoảng cách từ một điểm đến một đường thẳng.
- Vận dụng các công thức tính góc và khoảng cách để giải một số bài toán có liên quan đến thực tiến.

Trong mặt phẳng toạ độ, mỗi đường thẳng đều có đối tượng đại số tương ứng, gọi là phương trình của nó. Vậy các yếu tố liên quan tới đường thẳng được thể hiện như thế nào qua phương trình tương ứng?

# 1. VI TRÍ TƯƠNG ĐỐI GIỮA HAI ĐƯỜNG THẮNG

Ho1. Trong mặt phẳng toạ độ, cho hai đường thẳng

$$\Delta_1$$
:  $x - 2y + 3 = 0$ ,

$$\Delta_2$$
:  $3x - y - 1 = 0$ .

a) Điểm M(1; 2) có thuộc cả hai đường thẳng nói trên hay không?

b) Giải hệ 
$$\begin{cases} x - 2y + 3 = 0 \\ 3x - y - 1 = 0. \end{cases}$$

c) Chỉ ra mối quan hệ giữa toạ độ giao điểm của  $\Delta_1$  và  $\Delta_2$  với nghiệm của hệ phương trình trên.

Nhận xét. Mỗi đường thẳng trong mặt phẳng toạ độ là tập hợp những điểm có toạ độ thoả mãn phương trình của đường thẳng đó. Vì vậy, bài toán tìm giao điểm của hai đường thẳng được quy về bài toán giải hệ gồm hai phương trình tương ứng.

Trên mặt phẳng toạ độ, xét hai đường thẳng

$$\Delta_1$$
:  $a_1x + b_1y + c_1 = 0$  và  $\Delta_2$ :  $a_2x + b_2y + c_2 = 0$ .

Khi đó, toạ độ giao điểm của  $\Delta_1$  và  $\Delta_2$  là nghiệm của hệ phương trình:

$$\begin{cases} a_1 x + b_1 y + c_1 = 0 \\ a_2 x + b_2 y + c_2 = 0. \end{cases}$$
 (\*)

 $\Delta_1$  cắt  $\Delta_2$  tại  $M(x_0; y_0) \Leftrightarrow$  hệ (\*) có nghiệm duy nhất  $(x_0; y_0)$ .

 $\Delta_1$  song song với  $\Delta_2 \Leftrightarrow$  hệ (\*) vô nghiệm.

 $\Delta_1$  trùng  $\Delta_2 \Leftrightarrow \text{hệ (*) có vô số nghiệm.}$ 

## Chú ý

![](_page_37_Picture_1.jpeg)

 $\Delta_{t}$   $\Delta_{t}$   $\Delta_{t}$   $\Delta_{t}$   $\Delta_{t}$   $\Delta_{t}$   $\Delta_{t}$   $\Delta_{t}$   $\Delta_{t}$   $\Delta_{t}$   $\Delta_{t}$   $\Delta_{t}$   $\Delta_{t}$ 

Hình 7.5

Dựa vào các vectơ chỉ phương  $\overline{u_1}$ ,  $\overline{u_2}$  hoặc các vectơ pháp tuyến  $\overline{n_1}$ ,  $\overline{n_2}$  của  $\Delta_1$ ,  $\Delta_2$ , ta có:

- $\Delta_1$  và  $\Delta_2$  song song hoặc trùng nhau  $\Leftrightarrow \overline{u_1}$  và  $\overline{u_2}$  cùng phương  $\Leftrightarrow \overline{n_1}$  và  $\overline{n_2}$  cùng phương.
- $\Delta_1$  và  $\Delta_2$  cắt nhau  $\Leftrightarrow \overline{u_1}$  và  $\overline{u_2}$  không cùng phương  $\Leftrightarrow \overline{n_1}$  và  $\overline{n_2}$  không cùng phương.
- **)** Ví dụ 1. Xét vị trí tương đối giữa đường thẳng  $\Delta: x \sqrt{2}y + 4\sqrt{3} = 0$  và mỗi đường thẳng sau:

$$\Delta_1: \sqrt{3}x - \sqrt{6}y + 12 = 0;$$

$$\Delta_2: \sqrt{2}x - 2y = 0.$$

Giải

Vì 
$$x - \sqrt{2}y + 4\sqrt{3} = 0 \Leftrightarrow \sqrt{3}(x - \sqrt{2}y + 4\sqrt{3}) = 0$$
  
$$\Leftrightarrow \sqrt{3}x - \sqrt{6}y + 12 = 0.$$

Vậy Δ và Δ₁ là một, tức là chúng trùng nhau.

Hai đường thẳng  $\Delta$  và  $\Delta_2$  có hai vectơ pháp tuyến  $\overline{n}$ (1;  $-\sqrt{2}$ ) và  $\overline{n_2}$ ( $\sqrt{2}$ ; -2) cùng phương. Do đó, chúng song song hoặc trùng nhau. Mặt khác, điểm O(0; 0) thuộc đường thẳng  $\Delta_2$  nhưng không thuộc đường thẳng  $\Delta$ , nên hai đường thẳng này không trùng nhau. Vậy  $\Delta$  và  $\Delta_2$  song song với nhau.

Nhận xét. Giả sử hai đường thẳng  $\Delta_1$ ,  $\Delta_2$  có hai vectơ chỉ phương  $\overrightarrow{u_1}$ ,  $\overrightarrow{u_2}$  (hay hai vectơ pháp tuyến  $\overrightarrow{n_1}$ ,  $\overrightarrow{n_2}$ ) cùng phương. Khi đó:

- Nếu  $\Delta_1$  và  $\Delta_2$  có điểm chung thì  $\Delta_1$  trùng  $\Delta_2$ .
- Nếu tồn tại điểm thuộc  $\Delta_1$  nhưng không thuộc  $\Delta_2$  thì  $\Delta_1$  song song với  $\Delta_2$ .
- Luyện tập 1. Xét vị trí tương đối giữa các cặp đường thẳng sau:

a) 
$$\Delta_1: x + 4y - 3 = 0 \text{ và } \Delta_2: x - 4y - 3 = 0;$$

b) 
$$\Delta_1: x + 2y - \sqrt{5} = 0 \text{ và } \Delta_2: 2x + 4y - 3\sqrt{5} = 0$$
.

# 2. GÓC GIỮA HAI ĐƯỜNG THẮNG

) H92. Hai đường thẳng  $\Delta_1$  và  $\Delta_2$  cắt nhau tạo thành bốn góc (H.7.6). Các số đo của bốn góc đó có mối quan hệ gì với nhau?

![](_page_37_Picture_22.jpeg)

Hai đường thẳng cắt nhau tạo thành bốn góc, số đo của góc không tù được gọi là số đo góc (hay đơn giản là góc) giữa hai đường thẳng.

Góc giữa hai đường thẳng song song hoặc trùng nhau được quy ước bằng 0°.

 $bigcite{}$  HD3. Cho hai đường thẳng cắt nhau  $\Delta_1$ ,  $\Delta_2$  tương ứng có các vectơ pháp tuyến  $\overrightarrow{n_1}$ ,  $\overrightarrow{n_2}$  . Gọi φ là góc giữa hai đường thẳng đó (H.7.7). Nêu mối quan hệ giữa:

![](_page_38_Picture_3.jpeg)

b)  $\cos \varphi$  và  $\cos (\overline{n_1}, \overline{n_2})$ .

![](_page_38_Picture_5.jpeg)

![](_page_38_Picture_7.jpeg)

Cho hai đường thẳng

$$\Delta_1$$
:  $a_1x + b_1y + c_1 = 0$  và  $\Delta_2$ :  $a_2x + b_2y + c_2 = 0$ ,

với các vectơ pháp tuyến  $\overline{n_1}(a_1;b_1)$  và  $\overline{n_2}(a_2;b_2)$  tương ứng. Khi đó, góc φ giữa hai đường thẳng đó được xác định thông qua công thức

$$\cos \varphi = \left| \cos \left( \overrightarrow{n_1}, \overrightarrow{n_2} \right) \right| = \frac{\left| \overrightarrow{n_1} \cdot \overrightarrow{n_2} \right|}{\left| \overrightarrow{n_1} \right| \cdot \left| \overrightarrow{n_2} \right|} = \frac{\left| a_1 a_2 + b_1 b_2 \right|}{\sqrt{a_1^2 + b_1^2} \cdot \sqrt{a_2^2 + b_2^2}}.$$

- Chú ý  $\Delta_1 \perp \Delta_2 \Leftrightarrow \overrightarrow{n_1} \perp \overrightarrow{n_2} \Leftrightarrow a_1 a_2 + b_1 b_2 = 0.$  Nếu  $\Delta_1$ ,  $\Delta_2$  có các vectơ chỉ phương  $\overrightarrow{u_1}$ ,  $\overrightarrow{u_2}$  thì góc  $\phi$  giữa  $\Delta_1$  và  $\Delta_2$  cũng được xác định thông qua công thức  $\cos \varphi = \left|\cos \left(\overrightarrow{u_1}, \overrightarrow{u_2}\right)\right|$ .
- **)) ví dụ 2.** Tính góc giữa hai đường thẳng

$$\Delta_1$$
:  $\sqrt{3}x - y + 2 = 0$  và  $\Delta_2$ :  $x - \sqrt{3}y - 2 = 0$ .

Giải

Vector pháp tuyến của  $\Delta_1$  là  $\overrightarrow{n_1} = (\sqrt{3}; -1)$ , của  $\Delta_2$  là  $\overrightarrow{n_2} = (1; -\sqrt{3})$ .

Gọi  $\phi$  là góc giữa hai đường thẳng  $\Delta_{\rm 1}$  và  $\Delta_{\rm 2}.$  Ta có

$$\cos \varphi = \left| \cos \left( \overline{n_1}, \overline{n_2} \right) \right| = \frac{\left| \overline{n_1} \cdot \overline{n_2} \right|}{\left| \overline{n_1} \right| \cdot \left| \overline{n_2} \right|} = \frac{\left| \sqrt{3} \cdot 1 + (-1) \cdot (-\sqrt{3}) \right|}{\sqrt{(\sqrt{3})^2 + (-1)^2} \cdot \sqrt{1^2 + (-\sqrt{3})^2}} = \frac{\sqrt{3}}{2}.$$

Do đó, góc giữa  $\Delta_1$  và  $\Delta_2$  là  $\varphi = 30^\circ$ .

Duyện tập 2. Tính góc giữa hai đường thẳng

$$\Delta_1$$
:  $x + 3y + 2 = 0$  và  $\Delta_2$ :  $y = 3x + 1$ .

**))** Ví dụ 3. Tính góc giữa hai đường thẳng  $\Delta_1$ : x = 3 và  $\Delta_2$ :  $\begin{cases} x = 2 - t \\ v = 3 + t \end{cases}$ 

Đường thẳng  $\Delta_1$  có phương trình x-3=0 nên có vectơ pháp tuyến  $\overrightarrow{n_1}(1; 0)$ . Đường thẳng  $\Delta_2$  có vecto chỉ phương  $\overline{u_2}(-1; 1)$  nên có vecto pháp tuyến  $\overline{n_2}(1; 1)$ . Gọi  $\varphi$  là góc giữa hai đường thẳng  $\Delta_1$  và  $\Delta_2$ . Ta có

$$\cos \varphi = \left| \cos \left( \overrightarrow{n_1}, \overrightarrow{n_2} \right) \right| = \frac{\left| \overrightarrow{n_1} \cdot \overrightarrow{n_2} \right|}{\left| \overrightarrow{n_1} \right| \cdot \left| \overrightarrow{n_2} \right|} = \frac{\left| 1 \cdot 1 + 0 \cdot 1 \right|}{\sqrt{1^2 + 0^2} \cdot \sqrt{1^2 + 1^2}} = \frac{1}{\sqrt{2}}.$$

Do đó, góc giữa  $\Delta_1$  và  $\Delta_2$  là  $\varphi = 45^\circ$ .

**Luyện tập 3.** Tính góc giữa hai đường thẳng 
$$\Delta_1$$
: 
$$\begin{cases} x = 2 + t \\ y = 1 - 2t \end{cases}$$
 và  $\Delta_2$ : 
$$\begin{cases} x = 1 + t \\ y = 5 + 3t \end{cases}$$
.

Xét đường thẳng  $\Delta$  bất kì cắt trục hoành Ox tại một điểm A. Điểm A chia đường thẳng  $\Delta$ thành hai tia, trong đó, gọi Az là tia nằm phía trên trục hoành. Kí hiệu  $\alpha_{\scriptscriptstyle \Lambda}$  là số đo của góc xAz (H.7.8). Thực hành luyện tập sau đây, ta sẽ thấy ý nghĩa hình học của hệ số góc.

- **In Luyện tập 4.** Cho đường thẳng  $\Delta$ : y = ax + b, với  $a \neq 0$ .
  - a) Chứng minh rằng ∆ cắt trục hoành.
  - b) Lập phương trình đường thẳng  $\Delta_0$  đi qua O(0;0) và song song (hoặc trùng) với  $\Delta$ . c) Hãy chỉ ra mối quan hệ giữa  $\alpha_\Delta$  và  $\alpha_{\Delta_0}$ .

  - d) Gọi M là giao điểm của  $\Delta_0$  với nửa đường tròn đơn vị và  $x_0$  là hoành độ của M. Tính tung độ của M theo  $x_0$  và a. Từ đó, chứng minh rằng  $\tan \alpha_{\lambda} = a$ .

![](_page_39_Figure_13.jpeg)

Hình 7.8

# 3. KHOẢNG CÁCH TỪ MỘT ĐIỂM ĐẾN MỘT ĐƯỜNG THẮNG

- **) H04.** Cho điểm  $M(x_0; y_0)$  và đường thẳng  $\Delta$ : ax + by + c = 0 có vectơ pháp tuyến  $\vec{n}(a; b)$ . Gọi H là hình chiếu vuông góc của M trên  $\Delta$  (H 7.9).
  - a) Chứng minh rằng  $|\vec{n} \cdot \overrightarrow{HM}| = \sqrt{a^2 + b^2} \cdot HM$ .
  - b) Giả sử H có toạ độ  $(x_1; y_1)$ . Chứng minh rằng:

$$\vec{n} \cdot \overrightarrow{HM} = a(x_0 - x_1) + b(y_0 - y_1) = ax_0 + by_0 + c.$$

c) Chứng minh rằng  $HM = \frac{\left|ax_0 + by_0 + c\right|}{\sqrt{a^2 + b^2}}$ .

![](_page_40_Figure_6.jpeg)

Cho điểm  $M(x_0; y_0)$  và đường thẳng  $\Delta$ : ax + by + c = 0. Khoảng cách từ điểm M đến đường thẳng  $\Delta$ , kí hiệu là  $d(M, \Delta)$ , được tính bởi công thức

$$d(M,\Delta) = \frac{\left|ax_0 + by_0 + c\right|}{\sqrt{a^2 + b^2}}.$$

) Ví dụ 4. Tính khoảng cách từ điểm M(2; 4) đến đường thẳng  $\Delta$ : 3x + 4y - 12 = 0. Giải

Áp dụng công thức tính khoảng cách từ điểm M đến đường thẳng  $\Delta$ , ta có

$$d(M,\Delta) = \frac{|3 \cdot 2 + 4 \cdot 4 - 12|}{\sqrt{3^2 + 4^2}} = \frac{10}{5} = 2.$$

Vậy khoảng cách từ điểm M đến đường thẳng  $\Delta$  là 2.

**Trải nghiệm.** Đo trực tiếp khoảng cách từ điểm M đến đường thẳng  $\Delta$  (H 7.10) và giải thích vì sao kết quả đo đạc đó phù hợp với kết quả tính toán trong lời giải của Ví dụ 4.

![](_page_40_Figure_14.jpeg)

Hình 7.10

>> Luyện tập 5. Tính khoảng cách từ điểm M(1; 2) đến đường thẳng

$$\Delta: \begin{cases} x = 5 + 3t \\ y = -5 - 4t. \end{cases}$$

- Vận dụng. Nhân dịp nghỉ hè, Nam về quê ở với ông bà nội. Nhà ông bà nội có một ao cá có dạng hình chữ nhật ABCD với chiều dài AD = 15 m, chiều rộng AB = 12 m. Phần tam giác DEF là nơi ông bà nuôi vịt, AE = 5 m, CF = 6 m (H.7.11).
  - a) Chọn hệ trục toạ độ Oxy, có điểm O trùng với điểm B, các tia Ox, Oy tương ứng trùng với các tia BC, BA. Chọn 1 đơn vị độ dài trên mặt phẳng toạ độ tương ứng với 1 m trong thực tế. Hãy xác định toạ độ của các điểm A, B, C, D, E, F và viết phương trình đường thẳng EF.

![](_page_41_Figure_2.jpeg)

Hình 7.11

b) Nam đứng ở vị trí B câu cá và có thể quăng lưỡi câu xa 10,7 m. Hỏi lưỡi câu có thể rơi vào nơi nuôi vịt hay không?

# **BÀI TẬP**

7.7. Xét vị trí tương đối giữa các cặp đường thẳng sau:

a) 
$$\Delta_1: 3\sqrt{2}x + \sqrt{2}y - \sqrt{3} = 0 \ \forall \hat{a} \ \Delta_2: 6x + 2y - \sqrt{6} = 0.$$

b) 
$$d_1: x - \sqrt{3}y + 2 = 0$$
 và  $d_2: \sqrt{3}x - 3y + 2 = 0$ .

c) 
$$m_1: x-2y+1=0$$
  $\forall a m_2: 3x+y-2=0$ .

7.8. Tính góc giữa các cặp đường thẳng sau:

a) 
$$\Delta_1: \sqrt{3}x + y - 4 = 0 \ \forall \hat{a} \ \Delta_2: x + \sqrt{3}y + 3 = 0;$$

b) 
$$d_1$$
:  $\begin{cases} x = -1 + 2t \\ y = 3 + 4t \end{cases}$  và  $d_2$ :  $\begin{cases} x = 3 + s \\ y = 1 - 3s \end{cases}$  (t, s là các tham số).

- 7.9. Trong mặt phẳng toạ độ Oxy, cho điểm A(0; -2) và đường thẳng  $\Delta: x + y 4 = 0$ .
  - a) Tính khoảng cách từ điểm A đến đường thẳng  $\Delta$ .
  - b) Viết phương trình đường thẳng a đi qua điểm M(-1; 0) và song song với  $\Delta$ .
  - c) Viết phương trình đường thẳng b đi qua điểm N(0; 3) và vuông góc với  $\Delta$ .
- 7.10. Trong mặt phẳng toạ độ, cho tam giác ABC có A(1; 0), B(3; 2) và C(-2; -1).
  - a) Tính độ dài đường cao kẻ từ đỉnh A của tam giác ABC.
  - b) Tính diện tích tam giác ABC.
- 7.11. Chứng minh rằng hai đường thẳng  $d: y = ax + b \ (a \neq 0)$  và  $d': y = a'x + b' \ (a' \neq 0)$  vuông góc với nhau khi và chỉ khi aa' = -1.
- **7.12.** Trong mặt phẳng toạ độ, một tín hiệu âm thanh phát đi từ một vị trí và được ba thiết bị ghi tín hiệu đặt tại ba vị trí O(0;0), A(1;0), B(1;3) nhận được cùng một thời điểm. Hãy xác định vị trí phát tín hiệu âm thanh.

## ● Em có biết?

Cơ sở toán học cho các tính toán trong phần mềm GeoGebra.

![](_page_42_Figure_2.jpeg)

Hình 7.12

Hình 7.12 được chụp lại từ một màn hình máy tính đang sử dụng phần mềm vẽ hình GeoGebra:

- Chọn chức năng vẽ điểm, sau đó, nháy chuột vào ba điểm A, B, C trên cửa sổ màn hình, phần mềm tự động xác định toạ độ của ba điểm đó là A(2; 4), B(-4; 1), C(3; -2).
- Chọn chức năng vẽ đường thẳng  $\Delta$  đi qua hai điểm, sau đó, nháy vào hai điểm A, B ta được đường thẳng  $\Delta$  đi qua hai điểm A, B; phần mềm tự động xác định được phương trình của đường thẳng là x 2y + 6 = 0.
- Chọn chức năng tính khoảng cách, sau đó, nháy vào điểm C và đường thẳng  $\Delta$ , phần mềm sẽ tự động cho ta khoảng cách từ C tới đường thẳng  $\Delta$  là 5,81.

Cơ sở toán học để phần mềm có được tính toán nói trên là các công thức đã được nêu ra trong bài học này.

# ĐƯỜNG TRÒN TRONG MẶT PHẨNG TOẠ ĐỘ

## THUẬT NGỮ

- · Đường tròn
- Tâm
- Bán kính
- Phương trình đường tròn
- Phương trình tiếp tuyến

# KIẾN THỨC, KĨ NĂNG

- Lập phương trình đường tròn khi biết toạ độ tâm và bán kính hoặc biết toạ độ ba điểm thuộc đường tròn.
- Xác định tâm và bán kính của đường tròn khi biết phương trình của nó.
- Lập phương trình tiếp tuyến của đường tròn khi biết toạ độ của tiếp điểm.
- Vận dụng kiến thức về phương trình đường tròn để giải một số bài toán liên quan đến thực tiễn.

Cũng như đối với đường thẳng, việc đại số hoá đường tròn gồm hai bước:

- Thiết lập đối tượng đại số tương ứng với đường tròn, gọi là phương trình của đường tròn.
- Chuyển các yếu tố liên quan tới đường tròn từ hình học sang đại số.

## 1. PHƯƠNG TRÌNH ĐƯỜNG TRÒN

Đường tròn tâm I, bán kính R là tập hợp những điểm M thoả mãn điều kiện IM = R. Do đó, để lập phương trình đường tròn đó, ta cần chuyển điều kiện hình học IM = R thành một điều kiên đai số.

H91. Trong mặt phẳng toạ độ Oxy, cho đường tròn (C), tâm I(a; b), bán kính R (H.7.13). Khi đó, một điểm M(x; y) thuộc đường tròn (C) khi và chỉ khi toạ độ của nó thoả mãn điều kiện đại số nào?

![](_page_43_Figure_19.jpeg)

Hình 7.13

Điểm M(x; y) thuộc đường tròn (C), tâm I(a; b), bán kính R khi và chỉ khi

$$(x-a)^2 + (y-b)^2 = R^2.$$
 (1)

Ta gọi (1) là phương trình của đường tròn (C).

**Ví dụ 1.** Tìm tâm và bán kính của đường tròn (C) có phương trình:  $(x-2)^2 + (y+3)^2 = 16$ . Viết phương trình đường tròn (C') có tâm J(2; -1) và có bán kính gấp đôi bán kính đường tròn (C).

Giải

Ta viết phương trình của (C) ở dạng  $(x-2)^2 + (y-(-3))^2 = 4^2$ .

Vậy (C) có tâm I = (2, -3) và bán kính R = 4.

Đường tròn (C') có tâm J(2;-1) và có bán kính R'=2R=8 , nên có phương trình

$$(x-2)^2 + (y+1)^2 = 64.$$

**Luyện tập 1.** Tìm tâm và bán kính của đường tròn (C):  $(x+2)^2 + (y-4)^2 = 7$ .

Nhân xét. Phương trình (1) tương đương với

$$x^{2} + y^{2} - 2ax - 2by + (a^{2} + b^{2} - R^{2}) = 0.$$

**)** Ví dụ 2. Cho a, b, c là các hằng số. Tìm tập hợp những điểm M(x; y) thoả mãn phương trình

$$x^2 + y^2 - 2ax - 2by + c = 0. (2)$$

Giải

Phương trình (2) tương đương với

$$(x-a)^2 + (y-b)^2 + c - a^2 - b^2 = 0 \Leftrightarrow (x-a)^2 + (y-b)^2 = a^2 + b^2 - c$$

Xét I(a; b), khi đó,  $IM = \sqrt{(x-a)^2 + (y-b)^2}$  và phương trình trên trở thành

$$IM^2 = a^2 + b^2 - c. (3)$$

Từ đó, ta xét các trường hợp sau:

- Nếu  $a^2 + b^2 c > 0$  thì tập hợp những điểm M thoả mấn (2) là đường tròn tâm I(a; b), bán kính  $R = \sqrt{a^2 + b^2 c}$ .
- Nếu  $a^2 + b^2 c = 0$  thì (3)  $\Leftrightarrow IM = 0$ . Do đó, tập hợp những điểm M thoả mãn (2) chỉ gồm một điểm là I(a; b).
- Nếu  $a^2 + b^2 c < 0$  thì tập hợp những điểm *M* là tập rỗng.

Phương trình  $x^2 + y^2 - 2ax - 2by + c = 0$  là phương trình của một đường tròn (C) khi và chỉ khi  $a^2 + b^2 - c > 0$ . Khi đó, (C) có tâm l(a; b) và bán kính  $R = \sqrt{a^2 + b^2 - c}$ .

- Luyện tập 2. Hãy cho biết phương trình nào dưới đây là phương trình của một đường tròn và tìm tâm, bán kính của đường tròn tương ứng.
  - a)  $x^2 y^2 2x + 4y 1 = 0$ ;
  - b)  $x^2 + y^2 2x + 4y + 6 = 0$ ;
  - c)  $x^2 + y^2 + 6x 4y + 2 = 0$ .
- **>>> Ví dụ 3.** Viết phương trình đường tròn (*C*) đi qua ba điểm *A*(2; 0), *B*(0; 4), *C*(−7; 3).

Giải

Các đoạn thẳng AB, AC tương ứng có trung điểm là M(1; 2),  $N\left(-\frac{5}{2}; \frac{3}{2}\right)$ . Đường thẳng trung trực  $\Delta_1$  của đoạn thẳng AB đi qua M(1; 2) và có vectơ pháp tuyến  $\overrightarrow{AB}(-2; 4)$ .

Vì  $\overrightarrow{AB}(-2;4)$  cùng phương với  $\overrightarrow{n_1}(1;-2)$  nên  $\Delta_1$  cũng nhận  $\overrightarrow{n_1}(1;-2)$  là vectơ pháp tuyến. Do đó, phương trình của  $\Delta_1$  là

$$1(x-1)-2(y-2)=0$$
 hay  $x-2y+3=0$ .

Đường thẳng trung trực  $\Delta_2$  của đoạn thẳng AC đi qua  $N\left(-\frac{5}{2}; \frac{3}{2}\right)$  và có vectơ pháp tuyến  $\overrightarrow{AC}(-9; 3)$ .

Vì  $\overrightarrow{AC}(-9; 3)$  cùng phương với  $\overrightarrow{n_2}(3; -1)$  nên  $\Delta_2$  cũng nhận  $\overrightarrow{n_2}(3; -1)$  là vectơ pháp tuyến. Do đó, phương trình của  $\Delta_2$  là

$$3\left(x+\frac{5}{2}\right)-1\left(y-\frac{3}{2}\right)=0$$
 hay  $3x-y+9=0$ .

Tâm / của đường tròn (C) cách đều ba điểm A, B, C nên / là giao điểm của  $\Delta_1$  và  $\Delta_2$ .

Vậy toạ độ của / là nghiệm của hệ phương trình  $\begin{cases} x - 2y + 3 = 0 \\ 3x - y + 9 = 0. \end{cases}$ 

Suy ra I(-3; 0). Đường tròn (C) có bán kính là IA = 5. Vậy phương trình của (C) là  $(x + 3)^2 + y^2 = 25$ .

- **)** Luyện tập 3. Viết phương trình đường tròn (C) đi qua ba điểm M(4; -5), N(2; -1), P(3; -8).
- Vận dụng. Bên trong một hồ bơi, người ta dự định thiết kế hai bể sục nửa hình tròn bằng nhau và một bể sục hình tròn (H.7.14) để người bơi có thể ngồi tựa lưng vào thành các bể sục thư giãn. Hãy tìm bán kính của các bể sục để tổng chu vi của ba bể là 32 m mà tổng diện tích (chiếm hồ bơi) là nhỏ nhất. Trong tính toán, lấy π = 3,14, độ dài tính theo mét và làm tròn tới chữ số thập phân thứ hai.

## Hướng dẫn

Gọi bán kính bể hình tròn và bể nửa hình tròn tương ứng là
 x, y (m). Khi đó, tổng chu vi ba bể là 32 m khi và chỉ khi

$$1,57x + 2,57y - 8 = 0.$$

Gọi tổng diện tích của ba bể sục là S (m²). Khi đó

$$x^2 + y^2 = \frac{S}{3.14}$$
.

- Trong mặt phẳng toạ độ Oxy, xét đường tròn (C):  $x^2 + y^2 = \frac{S}{3,14}$  có tâm O(0; 0), bán kính  $R = \sqrt{\frac{S}{3,14}}$  và

đường thẳng  $\Delta$ : 1,57x + 2,57y - 8 = 0. Khi đó bài toán được chuyển thành: Tìm R nhỏ nhất để (C) và  $\Delta$  có ít nhất một điểm chung, với hoành độ và tung độ đều là các số dương (H.7.15).

![](_page_45_Picture_15.jpeg)

Hình 7.14

![](_page_45_Figure_17.jpeg)

Hình 7.15

# 2. PHƯƠNG TRÌNH TIẾP TUYỂN CỦA ĐƯỜNG TRÒN

- **) H92.** Cho đường tròn (*C*):  $(x-1)^2 + (y-2)^2 = 25$  và điểm M(4; -2).
  - a) Chứng minh điểm M(4; -2) thuộc đường tròn (C).
  - b) Xác định tâm và bán kính của (C).
  - c) Gọi  $\Delta$  là tiếp tuyến của (C) tại M. Hãy chỉ ra một vectơ pháp tuyến của đường thẳng  $\Delta$  (H.7.16). Từ đó, viết phương trình đường thẳng  $\Delta$ .

![](_page_46_Picture_5.jpeg)

Hinh 7.16

Cho điểm  $M(x_0; y_0)$  thuộc đường tròn (C):  $(x-a)^2 + (y-b)^2 = R^2$  (tâm I(a; b), bán kính R). Khi đó, tiếp tuyến  $\Delta$  của (C) tại  $M(x_0; y_0)$  có vectơ pháp tuyến  $\overrightarrow{MI} = (a - x_0; b - y_0)$  và phương trình

$$(a-x_0)(x-x_0)+(b-y_0)(y-y_0)=0.$$

**Ví dụ 4.** Cho đường tròn (C) có phương trình  $(x+1)^2 + (y-3)^2 = 5$ . Điểm M(0; 1) có thuộc đường tròn (C) hay không? Nếu có, hãy viết phương trình tiếp tuyến tại M của (C). **Giải** 

Do  $(0+1)^2 + (1-3)^2 = 5$ , nên điểm *M* thuộc (*C*).

Đường tròn (C) có tâm là I(-1; 3). Tiếp tuyến của (C) tại M(0; 1) có vectơ pháp tuyến  $\overrightarrow{MI} = (-1; 2)$ , nên có phương trình

$$-1(x-0)+2(y-1)=0 \Leftrightarrow x-2y+2=0.$$

VỚI CUỐC SỐNG

**Luyện tập 4.** Cho đường tròn (*C*):  $x^2 + y^2 - 2x + 4y + 1 = 0$ . Viết phương trình tiếp tuyến  $\triangle$  của (*C*) tại điểm N(1; 0).

# **BÀI TẬP**

7.13. Tìm tâm và tính bán kính của đường tròn

$$(x+3)^2 + (y-3)^2 = 36.$$

- 7.14. Hấy cho biết phương trình nào dưới đây là phương trình của một đường tròn và tìm tâm, bán kính của đường tròn tương ứng.
  - a)  $x^2 + y^2 + xy + 4x 2 = 0$ ;
  - b)  $x^2 + y^2 2x 4y + 5 = 0$ ;
  - c)  $x^2 + y^2 + 6x 8y + 1 = 0$ .

- 7.15. Viết phương trình của đường tròn (C) trong mỗi trường hợp sau:
  - a) Có tâm I(-2; 5) và bán kính R = 7;
  - b) Có tâm I(1; -2) và đi qua điểm A(-2; 2);
  - c) Có đường kính AB, với A(-1; -3), B(-3; 5);
  - d) Có tâm I(1; 3) và tiếp xúc với đường thẳng x + 2y + 3 = 0.
- **7.16.** Trong mặt phẳng toạ độ, cho tam giác ABC, với A(6; -2), B(4; 2), C(5; -5). Viết phương trình đường tròn ngoại tiếp tam giác đó.
- 7.17. Cho đường tròn (C):  $x^2 + y^2 + 2x 4y + 4 = 0$ . Viết phương trình tiếp tuyến d của (C) tại điểm M(0; 2).
- **7.18.** Chuyển động của một vật thể trong khoảng thời gian 180 phút được thể hiện trong mặt phẳng toạ độ. Theo đó, tại thời điểm t ( $0 \le t \le 180$ ) vật thể ở vị trí có toạ độ ( $2 + \sin t^{\circ}$ ;  $4 + \cos t^{\circ}$ ).
  - a) Tìm vị trí ban đầu và vị trí kết thúc của vật thể.
  - b) Tìm quỹ đạo chuyển động của vật thể.

# KẾT NỐI TRI THỰC VỚI CUỘC SỐNG

# Bài 22

# **BA ĐƯỜNG CONIC**

## THUẬT NGỮ

- Conic, Elip,
   Hypebol, Parabol
- Tiêu điểm
- Tiêu cư
- · Phương trình chính tắc
- Đường chuẩn, tham số tiêu

## KIẾN THỨC, KĨ NĂNG

- Nhận biết ba đường conic bằng hình học.
- Nhận biết phương trình chính tắc của ba đường conic.
- Giải quyết một số vấn đề thực tiễn gắn với ba đường conic.

![](_page_48_Picture_12.jpeg)

Hình 7.17

Trong thực tế, em có thể bắt gặp nhiều hình ảnh ứng với các đường elip (ellipse), hypebol (hyperbola), parabol (parabola), gọi chung là ba đường conic. Được phát hiện và nghiên cứu từ thời Hy Lạp cổ đại, nhưng các ứng dụng phong phú và quan trọng của các đường conic chỉ được phát hiện trong những thế kỉ gần đây, khởi đầu là định luật nổi tiếng của Kepler (Johannes Kepler, 1571–1630) về quỹ đạo của các hành tinh trong hệ Mặt Trời. Để có thể tiếp tục câu chuyện thú vị này, ta cần tìm hiểu kĩ hơn, đặc biệt là tìm phương trình đại số mô tả các đường conic.

## 1. ELIP

- HO1. Đính hai đầu của một sợi dây không đàn hồi vào hai vị trí cố định F<sub>1</sub>,F<sub>2</sub> trên một mặt bàn (độ dài sợi dây lớn hơn khoảng cách giữa hai điểm F<sub>1</sub>, F<sub>2</sub>). Kéo căng sợi dây tại một điểm M bởi một đầu bút dạ (hoặc phấn). Di chuyển đầu bút dạ để nó vẽ trên mặt bàn một đường khép kín (H.7.18).
  - a) Đường vừa nhận được có liên hệ với hình ảnh nào ở Hình 7.17?
  - b) Trong quá trình đầu bút di chuyển để vẽ nên đường nói trên, tổng các khoảng cách từ nó tới các vị trí  $F_1$ ,  $F_2$  có thay đổi không? Vì sao?

![](_page_48_Picture_19.jpeg)

Hình 7.18

Cho hai điểm cố định và phân biệt  $F_1$ ,  $F_2$ . Đặt  $F_1F_2=2c>0$ . Cho số thực a lớn hơn c. Tập hợp các điểm M sao cho  $MF_1+MF_2=2a$  được gọi là đường elip (hay elip). Hai điểm  $F_1$ ,  $F_2$  được gọi là hai tiêu điểm và  $F_1F_2=2c$  được gọi là tiêu cự của elip đó.

![](_page_49_Picture_1.jpeg)

Ví dụ 1. Cho lục giác đều ABCDEF. Chứng minh rằng bốn điểm B, C, E, F cùng thuộc một elip có hai tiêu điểm là A và D.

#### Giải

Lục giác đều ABCDEF có các cạnh bằng nhau và các góc đều có số đo là 120° (H.7.19). Do đó, các tam giác ABC, BCD, DEF, EFA bằng nhau (c.g.c). Suy ra AC = BD = DF = AE. Từ đó, ta có BA + BD = CA + CD = EA + ED = FA + FD > AD. Vậy B, C, E, F cùng thuộc một elip có hai tiêu điểm là A và D.

![](_page_49_Figure_5.jpeg)

![](_page_49_Figure_6.jpeg)

- a) Nêu toạ độ của các tiêu điểm  $F_1$ ,  $F_2$ .
- b) Giải thích vì sao điểm M(x;y) thuộc elip khi và chỉ khi

$$\sqrt{(x+c)^2+y^2}+\sqrt{(x-c)^2+y^2}=2a.$$
 (1)

![](_page_49_Figure_10.jpeg)

![](_page_49_Figure_11.jpeg)

![](_page_49_Figure_12.jpeg)

Chú ý. Người ta có thể biến đổi (1) về dạng  $\frac{x^2}{a^2} + \frac{y^2}{b^2} = 1$ , với  $b = \sqrt{a^2 - c^2}$ .

Trong mặt phẳng toạ độ *Oxy*, elip có hai tiêu điểm thuộc trục hoành sao cho *O* là trung điểm của đoạn nối hai tiêu điểm đó, thì có phương trình

$$\frac{x^2}{a^2} + \frac{y^2}{b^2} = 1, \text{ V\'oi} \ \ a > b > 0.$$
 (2)

Ngược lại, mỗi phương trình có dạng (2), với a > b > 0, đều là phương trình của elip có hai tiêu điểm  $F_1(-\sqrt{a^2-b^2}; 0)$ ,  $F_2(\sqrt{a^2-b^2}; 0)$ , tiêu cự  $2c = 2\sqrt{a^2-b^2}$  và tổng các khoảng cách từ mỗi điểm thuộc elip đó tới hai tiêu điểm bằng 2a.

Phương trình (2) được gọi là phương trình chính tắc của elip tương ứng.

**Ví dụ 2.** Cho elip có phương trình chính tắc  $\frac{x^2}{25} + \frac{y^2}{16} = 1$ . Tìm các tiêu điểm và tiêu cự của elip. Tính tổng các khoảng cách từ mỗi điểm trên elip tới hai tiêu điểm.

Ta có:  $a^2 = 25$ ,  $b^2 = 16$ . Do đó  $c = \sqrt{a^2 - b^2} = 3$ . Vậy elip có hai tiêu điểm là  $F_1(-3;0)$ ;  $F_2(3;0)$  và tiêu cự là  $F_1F_2 = 2c = 6$ . Ta có  $a = \sqrt{25} = 5$ , nên tổng các khoảng cách từ mỗi điểm trên elip tới hai tiêu điểm bằng 2a = 10.

- **Luyện tập 2.** Cho elip có phương trình chính tắc  $\frac{x^2}{100} + \frac{y^2}{64} = 1$ . Tìm các tiêu điểm và tiêu cự của elip.
- >>> Vận dụng 1. Trong bản vẽ thiết kế, vòm của ô thoáng trong Hình 7.22 là nửa nằm phía trên trục hoành của elip có phương trình

$$\frac{x^2}{16} + \frac{y^2}{4} = 1.$$

Biết rằng 1 đơn vị trên mặt phẳng toạ độ của bản vẽ thiết kế ứng với 30 cm trên thực tế. Tính chiều cao *h* của ô thoáng tại điểm cách điểm chính giữa của đế ô thoáng 75 cm.

![](_page_50_Figure_6.jpeg)

## 2. HYPEBOL

Giải

Trên mặt phẳng, nếu hai thiết bị đặt tại các vị trí  $F_1$ ,  $F_2$  nhận được một tín hiệu âm thanh cùng lúc thì vị trí phát ra tín hiệu cách đều  $F_1$  và  $F_2$ , do đó, nằm trên đường trung trực của đoạn thẳng  $F_1F_2$ . Nếu hai thiết bị nhận được tín hiệu không cùng lúc thì để giới hạn khu vực tìm kiếm nơi phát ra tín hiệu, ta cần biết một đối tượng toán học, gọi là hypebol.

![](_page_50_Picture_9.jpeg)

Cho hai điểm phân biệt cố định  $F_1$  và  $F_2$ . Đặt  $F_1F_2=2c$ . Cho số thực dương a nhỏ hơn c. Tập hợp các điểm M sao cho  $\left|MF_1-MF_2\right|=2a$  được gọi là <mark>đường hypebol</mark> (hay hypebol). Hai điểm  $F_1$ ,  $F_2$  được gọi là hai *tiêu điểm* và  $F_1F_2=2c$  được gọi là *tiêu cự* của hypebol đó.

 $\alpha$ Tại sao trong định nghĩa hypebol cần điều kiện a < c?

Chú ý. Hypebol có hai nhánh (H.7.23), một nhánh gồm những điểm M thoả mãn  $MF_1 - MF_2 = 2a$  và nhánh còn lại gồm những điểm M thoả mãn  $MF_1 - MF_2 = -2a$  (hay  $MF_2 - MF_1 = 2a$ ).

**>> Ví du 3.** Trên biển có hai đảo hình tròn với bán kính khác nhau. Tai vùng biển giữa hai đảo đó, người ta xác định một đường ranh giới cách đều hai đảo, tức là, đường mà khoảng cách từ mỗi vị trí trên đó đến hai đảo là bằng nhau. Hỏi đường ranh giới đó có thuộc một nhánh của một hypebol hay không?

Chú ý. Khoảng cách từ một vị trí trên biển đến đảo hình tròn bằng hiệu của khoảng cách từ vi trí đó đến tâm đảo và bán kính của đảo.

Giải. Giả sử đảo thứ nhất có tâm O<sub>4</sub> và bán kính R<sub>4</sub>, đảo thứ hai có tâm  $O_2$  và bán kính  $R_2$  (H.7.24). Do hai đường tròn  $(O_1, R_1)$ ,  $(O_2, R_2)$  nằm ngoài nhau nên  $O_1O_2 > R_1 + R_2$ . Gọi M là một điểm bất kì thuộc đường ranh giới.

Vì M cách đều hai đảo nên

$$MO_1 - R_1 = MO_2 - R_2 \Leftrightarrow MO_1 - MO_2 = R_1 - R_2$$
.

Vậy đường ranh giới thuộc một nhánh của hypebol với tiêu  $\vec{\text{diem}} \ F_1 \ \text{trung} \ O_1, \ F_2 \ \text{trung} \ O_2, \ 2c = O_1O_2, \ 2a = |R_1 - R_2|.$ 

![](_page_51_Figure_6.jpeg)

![](_page_51_Figure_7.jpeg)

$$\sqrt{(x+c)^2+y^2}-\sqrt{(x-c)^2+y^2}=2a.$$
 (3)

Chú ý. Người ta có thể biến đổi (3) về dạng

$$\frac{x^2}{a^2} - \frac{y^2}{b^2} = 1$$
, với  $b = \sqrt{c^2 - a^2}$ .

![](_page_51_Figure_11.jpeg)

Hình 7.24

![](_page_51_Figure_13.jpeg)

Hình 7.25

![](_page_51_Figure_15.jpeg)

Hình 7.26

Trong mặt phẳng toạ độ Oxy, hypebol có hai tiêu điểm thuộc trục hoành sao cho O là trung điểm của đoạn nối hai tiêu điểm đó, thì có phương trình

$$\frac{x^2}{a^2} - \frac{y^2}{b^2} = 1, \text{ V\'oi } a, b > 0.$$
 (4)

Ngược lại, mỗi phương trình có dạng (4), với a, b > 0, đều là phương trình của hypebol có hai tiêu điểm  $F_1(-\sqrt{a^2+b^2};0)$ ,  $F_2(\sqrt{a^2+b^2};0)$ , tiêu cự  $2c=2\sqrt{a^2+b^2}$  và giá trị tuyệt đối của hiệu các khoảng cách từ mỗi điểm thuộc hypebol đến hai tiêu điểm bằng 2a.

Phương trình (4) được gọi là phương trình chính tắc của hypebol tương ứng.

**Ví dụ 4.** Cho hypebol có phương trình chính tắc  $\frac{x^2}{9} - \frac{y^2}{16} = 1$ . Tìm các tiêu điểm và tiêu cự của hypebol. Hiệu các khoảng cách từ một điểm nằm trên hypebol tới hai tiêu điểm có giá trị tuyệt đối bằng bao nhiêu?

### Giải

Ta có  $a^2 = 9$ ,  $b^2 = 16$ , nên  $c = \sqrt{a^2 + b^2} = 5$ . Vậy hypebol có hai tiêu điểm là  $F_1(-5; 0)$ ,  $F_2(5; 0)$  và có tiêu cự 2c = 10. Hiệu các khoảng cách từ một điểm nằm trên hypebol tới hai tiêu điểm có giá trị tuyệt đối bằng  $2a = 2\sqrt{9} = 6$ .

**Luyện tập 4.** Cho (H):  $\frac{x^2}{144} - \frac{y^2}{25} = 1$ . Tìm các tiêu điểm và tiêu cự của (H).

## 3. PARABOL

**H94.** Cho parabol (*P*): 
$$y = \frac{1}{4}x^2$$
. Xét  $F(0; 1)$  và đường thẳng  $\Delta$ :  $y + 1 = 0$ . Với điểm  $M(x; y)$  bất kì, chứng minh rằng  $MF = d(M, \Delta) \Leftrightarrow M(x; y)$  thuộc (*P*).

Như vậy, parabol (*P*):  $y = \frac{1}{4}x^2$  là tập hợp những điểm cách đều điểm F(0; 1) và đường thẳng  $\Delta$ : y + 1 = 0.

![](_page_52_Picture_7.jpeg)

![](_page_52_Picture_8.jpeg)

Cho một điểm F cố định và một đường thẳng  $\Delta$  cố định không đi qua F. Tập hợp các điểm M cách đều F và  $\Delta$  được gọi là **đường parabol** (hay parabol). Điểm F được gọi là *tiêu điểm*,  $\Delta$  được gọi là **đường chuẩn**, khoảng cách từ F đến  $\Delta$  được gọi là tham số tiêu của parabol đó.

- ▶ H95. Xét (P) là một parabol với tiêu điểm F và đường chuẩn ∆. Gọi p là tham số tiêu của (P) và H là hình chiếu vuông góc của F trên ∆. Chọn hệ trục toạ độ Oxy có gốc O là trung điểm của HF, tia Ox trùng tia OF (H.7.27).
  - a) Nêu toạ độ của F và phương trình của  $\Delta$ .
  - b) Giải thích vì sao điểm M(x; y) thuộc (P) khi và chỉ khi

$$\sqrt{\left(x-\frac{p}{2}\right)^2+y^2}=\left|x+\frac{p}{2}\right|.$$

![](_page_52_Figure_14.jpeg)

Chú ý. Bình phương hai vế của phương trình cuối cùng trong HĐ5 rồi rút gọn, ta dễ dàng nhận được phương trình  $y^2 = 2px$ .

Xét (P) là một parabol với tiêu điểm F, đường chuẩn  $\Delta$ . Gọi H là hình chiếu vuông góc của F trên  $\Delta$ . Khi đó, trong hệ trục toạ độ Oxy với gốc O là trung điểm của HF, tia Ox trùng tia OF, parabol (P) có phương trình

$$y^2 = 2px \ (v \acute{o}i \ p > 0).$$
 (5)

Phương trình (5) được gọi là phương trình chính tắc của parabol (P).

Ngược lại, mỗi phương trình dạng (5), với p>0, là phương trình chính tắc của parabol có tiêu điểm  $F\left(\frac{p}{2};\ 0\right)$  và đường chuẩn  $\Delta:\ x=-\frac{p}{2}.$ 

- **)** Ví dụ 5. Cho parabol (P):  $y^2 = x$ .
  - a) Tìm tiêu điểm F, đường chuẩn  $\triangle$  của (P).
  - b) Tìm những điểm trên (P) có khoảng cách tới F bằng 3.

### Giài

a) Ta có 2p = 1 nên  $p = \frac{1}{2}$ . Parabol có tiêu điểm  $F\left(\frac{1}{4}; 0\right)$  và đường chuẩn  $\Delta$ :  $x = -\frac{1}{4}$ .

![](_page_53_Picture_9.jpeg)

![](_page_53_Picture_10.jpeg)

b) Điểm  $M(x_0; y_0)$  thuộc (P) có khoảng cách tới F bằng 3 khi và chỉ khi  $y_0^2 = x_0$  và MF = 3. Do  $MF = d(M, \Delta)$  nên  $d(M, \Delta) = 3$ .

Mặt khác 
$$\Delta: x + \frac{1}{4} = 0$$
 và  $x_0 = y_0^2 \ge 0$  nên  $3 = d(M, \Delta) = \left| x_0 + \frac{1}{4} \right| = x_0 + \frac{1}{4}$ 

Vậy 
$$x_0 = \frac{11}{4}$$
 và  $y_0 = \frac{\sqrt{11}}{2}$  hoặc  $y_0 = -\frac{\sqrt{11}}{2}$ .

Vậy có hai điểm M thoả mãn bài toán với toạ độ là  $\left(\frac{11}{4}; \frac{\sqrt{11}}{2}\right)$  và  $\left(\frac{11}{4}; -\frac{\sqrt{11}}{2}\right)$ .

Vận dụng 2. Tại một vùng biển giữa đất liền và một đảo, người ta phân định một đường ranh giới cách đều đất liền và đảo (H.7.28). Coi bờ biển vùng đất liền đó là một đường thẳng và đảo là hình tròn. Hỏi đường ranh giới nói trên có hình gì? Vì sao?

![](_page_53_Picture_16.jpeg)

Hình 7.28

# 4. MỘT SỐ ỨNG DUNG CỦA BA ĐƯỜNG CONIC

## TÍNH CHẤT QUANG HỌC

Tương tư gương cầu lồi thường đặt ở những khúc đường cua, người ta cũng có những gương (lồi, lõm) elip, hypebol, parabol. Tia sáng gặp các gương này, đều được phản xạ theo một quy tắc được xác định rõ bằng hình học, chẳng hạn:

• Tia sáng phát ra từ một tiêu điểm của elip, hypebol (đối với các gương lõm elip, hypebol) sau khi gặp elip, hypebol sẽ bị hắt lại theo một tia (tia phản xa) nằm trên đường thẳng đi qua tiêu điểm còn lai (H.7.29).

![](_page_54_Picture_4.jpeg)

Tia sáng hướng tới một tiêu điểm của elip, hypebol (đối với các gương elip, hypebol lồi), khi gặp elip, hypebol sẽ bị hắt lại theo một tia nằm trên đường thẳng đi qua tiêu điểm còn lai (H.7.30).

![](_page_54_Picture_7.jpeg)

Với gương parabol lõm, tia sáng phát ra từ tiêu điểm khi gặp parabol sẽ bị hắt lại theo một tia vuông góc với đường chuẩn của parabol (H.7.31). Ngược lại, nếu tia tới vuông góc với đường chuẩn của parabol thì tia phản xạ sẽ đi qua tiêu điểm của parabol.

Tính chất quang học được đề cập ở trên giúp ta nhận được ánh sáng mạnh hơn khi các tia sáng hội tụ và giúp ta đổi hướng ánh sáng khi cần. Ta cũng có điều tương tự đối với tín hiệu âm thanh, tín hiệu truyền từ vệ tinh.

![](_page_54_Picture_10.jpeg)

Hình 7.31

## MÔT SỐ ỨNG DUNG

![](_page_55_Picture_1.jpeg)

Nhà vòm hoa (Flower Dome) trong Khu vườn bên vịnh (Gardens by the Bay), Singapore

![](_page_55_Picture_3.jpeg)

Công viên với hình elip ở phía nam Nhà Trắng, Hoa Kỳ

Ba đường conic xuất hiện và có nhiều ứng dụng trong khoa học và trong cuộc sống, chẳng hạn:

- Tia nước bắn ra từ đài phun nước, đường đi bổng của quả bóng là những hình ảnh về đường parabol;
- Khi nghiêng cốc tròn, mặt nước trong cốc có hình elip. Tương tự, dưới ánh sáng mặt trời, bóng của một quả bóng, nhìn chung, là một elip;
- Ánh sáng phát ra từ một bóng đèn Led trên trần nhà có thể tạo nên trên tường các nhánh hypebol;
- Nhiều công trình kiến trúc có hình elip, parabol hay hypebol.

![](_page_55_Picture_10.jpeg)

- Trong vũ trụ bao la, ánh sáng đóng vai trò sứ giả truyền tin. Ánh sáng phát ra từ một thiên thể sẽ mang những thông tin về nơi nó xuất phát. Khi nhận được ánh sáng, các nhà khoa học sẽ dựa vào đó để nghiên cứu, khám phá thiên thể. Trong thiên văn học, các gương trong kính thiên văn (H.7.32a) giúp nhà khoa học nhận được hình ảnh quan sát rõ nét hơn, ánh sáng thu được có các chỉ số phân tích rõ hơn.
- Anten vệ tinh parabol (H.7.32b) là thiết bị thu tín hiệu truyền về từ vệ tinh. Tín hiệu sau khi gặp parabol bị hắt lại và hội tụ về điểm thu được đặt tại tiêu điểm của parabol.
- Đèn pha đáy parabol (H.7.32c) giúp ánh sáng có thể phát xa (chẳng hạn, giúp đèn ô tô có thể chiếu xa). Ánh sáng xuất phát từ vị trí tiêu điểm của parabol, chiếu vào đáy đèn, các tia sáng bị hắt lại thành các tia sáng nằm trên các đường thẳng song song.
- Trong y học, để tán sỏi thận, người ta có thể dùng chùm tia laser phát ra từ một tiêu điểm của gương elip để sau khi phản xạ sẽ hội tụ tại tiêu điểm còn lại cũng chính là vị trí sỏi.
- Tháp giải nhiệt hình hypebol trong lò phản ứng hạt nhân (H.7.17c) hay trong nhà máy nhiệt điện có kiến trúc đảm bảo độ vững chãi, tiết kiệm nguyên vật liệu và giúp quá trình toả nhiệt được thuận lợi.

- Bằng các quan sát và phân tích thiên văn, Johannes Kepler (1571 1630) đã đưa ra định luật nói rằng, các hành tinh trong hệ Mặt Trời chuyển động theo các quỹ đạo là các đường elip nhân tâm Mặt Trời là một tiêu điểm.
- Vận dụng 3. Gương elip trong một máy tán sỏi thận (H.7.33) ứng với elip có phương trình chính tắc x²/400 + y²/76 = 1 (theo đơn vị cm). Tính khoảng cách từ vị trí đầu phát sóng của máy đến vị trí của sỏi thận cần tán.

![](_page_56_Figure_2.jpeg)

# **BÀI TẬP**

- 7.19. Cho elip có phương trình:  $\frac{x^2}{36} + \frac{y^2}{9} = 1$ . Tìm tiêu điểm và tiêu cự của elip.
- 7.20. Cho hypebol có phương trình:  $\frac{x^2}{7} \frac{y^2}{9} = 1$ . Tìm tiêu điểm và tiêu cự của hypebol.
- 7.21. Cho parabol có phương trình:  $y^2 = 8x$ . Tìm tiêu điểm và đường chuẩn của parabol.
- 7.22. Lập phương trình chính tắc của elip đi qua điểm A(5; 0) và có một tiêu điểm là  $F_2(3; 0)$ .
- 7.23. Lập phương trình chính tắc của parabol đi qua điểm M(2; 4).
- 7.24. Có hai trạm phát tín hiệu vô tuyến đặt tại hai vị trí A, B cách nhau 300 km. Tại cùng một thời điểm, hai trạm cùng phát tín hiệu với vận tốc 292 000 km/s để một tàu thuỷ thu và đo độ lệch thời gian. Tín hiệu từ A đến sớm hơn tín hiệu từ B là 0,0005 s. Từ thông tin trên, ta có thể xác định được tàu thuỷ thuộc đường hypebol nào? Viết phương trình chính tắc của hypebol đó theo đơn vị kilômét.
- 7.25. Khúc cua của một con đường có dạng hình parabol, điểm đầu vào khúc cua là A, điểm cuối là B, khoảng cách AB = 400 m. Đỉnh parabol (P) của khúc cua cách đường thẳng AB một khoảng 20 m và cách đều A, B (H.7.34).
  - a) Lập phương trình chính tắc của (*P*), với 1 đơn vị đo trong mặt phẳng toạ độ tương ứng 1 m trên thực tế.
  - b) Lập phương trình chính tắc của (*P*), với 1 đơn vị đo trong mặt phẳng toạ đô tương ứng 1 km trên thực tế.

![](_page_56_Figure_13.jpeg)

Hình 7.34

## Em có biết?

Hệ thống định vị trên mặt đất LORAN (Long Range Navigation) được hoạt động dựa trên nguyên lí đo sự chênh lệch thời gian tiếp nhận tín hiệu và sử dụng tính chất của hypebol để xác định vị trí của nơi nhận tín hiệu. Ta có thể hình dung một tình huống đơn giản như sau: Hai trạm phát sóng radio đặt tại hai vị trí xác định A, B, cùng lúc phát tín hiệu và được một tàu thuỷ thu và đo độ lệch về thời gian tiếp nhận. Từ vận tốc truyền sóng, có thể xác định được hiệu khoảng cách từ tàu thuỷ đến các vị trí A, B. Như vậy,

tàu thuỷ nằm trên một nhánh hypebol hoàn toàn xác định. Tương tự, nếu có trạm phát sóng thứ ba C (hoặc một cặp trạm C, D), thì cặp trạm phát sóng A, C (hay C, D), cũng cho phép ta xác định một nhánh hypebol đi qua vị trí tàu thuỷ. Do đó, vị trí tàu thuỷ được xác định như là giao điểm của hai nhánh hypebol (H.7.35a).

![](_page_57_Picture_1.jpeg)

Nền tảng toán học cho ứng dụng trên đã được biết đến từ hơn 2 000 năm trước. Bài toán xác định đường tròn tiếp xúc với ba đường tròn cho trước đã được đặt ra và nghiên cứu bởi Apollonius (khoảng 262-190, TCN). Trong Hình 7.35c, với ba đường tròn màu đen cho trước, đôi một ngoài nhau, có tám đường tròn tiếp xúc với cả ba đường tròn đó mà ta có thể đếm được trên hình vẽ. Nói chung, bài toán Apollonius có tám nghiệm hình, tuy vậy, trong một số trường hợp đặc biệt, số nghiệm có thể khác. Trong Hình 7.35b, với ba đường tròn đôi một tiếp xúc ngoài với nhau cho trước (ba hình tròn được tô cùng màu), có hai đường tròn tiếp xúc với chúng. Gọi  $r_1$ ,  $r_2$ ,  $r_3$  là bán kính của ba đường tròn cho trước trong Hình 7.35b và r, R (r < R) là bán kính của hai đường tròn nghiệm. Năm 1643, trong một bức thư gửi công chúa Elisabeth (1618-1680), Descartes (1596-1650) đã đưa ra các công thức sau, cho phép tính bán kính của các đường tròn nghiệm theo các đường tròn đã cho

$$\left(\frac{1}{r_1} + \frac{1}{r_2} + \frac{1}{r_3} + \frac{1}{r}\right)^2 = 2\left(\frac{1}{r_1^2} + \frac{1}{r_2^2} + \frac{1}{r_3^2} + \frac{1}{r^2}\right) \text{ và } \left(\frac{1}{r_1} + \frac{1}{r_2} + \frac{1}{r_3} - \frac{1}{R}\right)^2 = 2\left(\frac{1}{r_1^2} + \frac{1}{r_2^2} + \frac{1}{r_3^2} + \frac{1}{R^2}\right).$$

Định lí của Descartes còn được phát hiện một cách độc lập bởi Steiner năm 1826, Beecroft năm 1842, Soddy năm 1936. Soddy đã công bố phát hiện của mình trên tạp chí Nature dưới dạng một bài thơ với tên "The Kiss Precise".

Các thông tin trên cũng được đề cập trong bài báo của Coxter trên tạp chí American Mathematical Monthly, số 75, năm 1968.

Bài toán Apollonius còn được hiểu theo nghĩa rộng hơn, ở đó, ba đường cho trước có thể là đường tròn, đường thẳng, hay điểm. Để một đường tròn tiếp xúc ngoài (tiếp xúc trong) với hai đường tròn cho trước, thì tâm của nó phải thuộc một nhánh hypebol (hoặc elip). Do đó việc xác định tâm của đường tròn nghiệm của bài toán Apollonius có thể chuyển thành bài toán xác định giao của hai đường conic. Ta hoàn toàn có thể nhìn ra mối liên hệ giữa bài toán Apollonius với Ví dụ 3, Vận dụng 2 trong Bài 22, cũng như bài toán định vị trong hệ thống LORAN.

# BÀI TẬP CUỐI CHƯƠNG VII

# A - TRẮC NGHIỆM

7.26. Phương trình nào sau đây là phương trình tham số của đường thẳng?

**A** 
$$2x - y + 1 = 0$$
.

**B.** 
$$\begin{cases} x = 2t \\ y = t \end{cases}$$
 **C.**  $x^2 + y^2 = 1$ .

D. 
$$y = 2x + 3$$
.

7.27. Phương trình nào sau đây là phương trình tổng quát của đường thẳng?

$$-x-2y+3=0.$$

B. 
$$\begin{cases} x = 2 + t \\ y = 3 - t \end{cases}$$
 C.  $y^2 = 2x$ .

C. 
$$y^2 = 2x$$
.

$$D. \frac{x^2}{10} + \frac{y^2}{6} = 1.$$

7.28. Phương trình nào sau đây là phương trình của đường tròn?

$$A x^2 - y^2 = 1.$$

**B.** 
$$(x-1)^2 + (y-2)^2 = -4$$
.

C. 
$$x^2 + y^2 = 2$$
.

D. 
$$y^2 = 8x$$
.

7.29. Phương trình nào sau đây là phương trình chính tắc của đường elip?

**A.** 
$$\frac{x^2}{9} + \frac{y^2}{9} = 1$$
.

**B.** 
$$\frac{x^2}{1} + \frac{y^2}{6} = 1$$
.

**B.** 
$$\frac{x^2}{1} + \frac{y^2}{6} = 1$$
. **C.**  $\frac{x^2}{4} - \frac{y^2}{1} = 1$ . **D.**  $\frac{x^2}{2} + \frac{y^2}{1} = 1$ .

D. 
$$\frac{x^2}{2} + \frac{y^2}{1} = 1$$

7.30. Phương trình nào sau đây là phương trình chính tắc của đường hypebol?

A 
$$\frac{x^2}{3} - \frac{y^2}{2} = -1$$
.

**B.** 
$$\frac{x^2}{1} - \frac{y^2}{6} = 1$$
.

C. 
$$\frac{x^2}{6} + \frac{y^2}{1} = 1$$
.

**B.** 
$$\frac{x^2}{1} - \frac{y^2}{6} = 1$$
. **C.**  $\frac{x^2}{6} + \frac{y^2}{1} = 1$ . **D.**  $\frac{x^2}{2} + \frac{y^2}{1} = -1$ .

7.31. Phương trình nào sau đây là phương trình chính tắc của đường parabol?

**A** 
$$x^2 = 4y$$
.

**B.** 
$$x^2 = -6y$$
. **C.**  $y^2 = 4x$ .

C. 
$$y^2 = 4x$$

**D.** 
$$y^2 = -4x$$
.

# **B-TU LUÂN**

7.32. Trong mặt phẳng toạ độ, cho A(1; -1), B(3; 5), C(-2; 4). Tính diện tích tam giác ABC.

VỚI CUỐC SỐNG

7.33. Trong mặt phẳng toạ độ, cho hai điểm A(-1; 0) và B(3; 1).

- a) Viết phương trình đường tròn tâm A và đi qua B.
- b) Viết phương trình tổng quát của đường thẳng AB.
- c) Viết phương trình đường tròn tâm O và tiếp xúc với đường thẳng AB.

**7.34.** Cho đường tròn (C) có phương trình  $x^2 + y^2 - 4x + 6y - 12 = 0$ .

a) Tìm toạ độ tâm I và bán kính R của (C).

b) Chứng minh rằng điểm M(5; 1) thuộc (C). Viết phương trình tiếp tuyến d của (C) tại M.

- 7.35. Cho elip (E):  $\frac{x^2}{a^2} + \frac{y^2}{b^2} = 1 \ (a > b > 0).$ 
  - a) Tìm các giao điểm  $A_1$ ,  $A_2$  của (E) với trục hoành và các giao điểm  $B_1$ ,  $B_2$  của (E) với trục tung. Tính  $A_1A_2$ ,  $B_1B_2$ .
  - b) Xét một điểm bất kì  $M(x_0, y_0)$  thuộc (E).

Chứng minh rằng,  $b^2 \le x_0^2 + y_0^2 \le a^2$  và  $b \le OM \le a$ .

Chú ý.  $A_1A_2$ ,  $B_1B_2$  tương ứng được gọi là trục lớn, trục nhỏ của elip (E) và tương ứng có độ dài là 2a, 2b.

- 7.36. Cho hypebol có phương trình:  $\frac{x^2}{a^2} \frac{y^2}{b^2} = 1$ .
  - a) Tìm các giao điểm  $A_1$ ,  $A_2$  của hypebol với trục hoành (hoành độ của  $A_1$  nhỏ hơn của  $A_2$ ).
  - b) Chứng minh rằng, nếu điểm M(x; y) thuộc nhánh nằm bên trái trục tung của hypebol thì  $x \le -a$ , nếu điểm M(x; y) thuộc nhánh nằm bên phải trục tung của hypebol thì  $x \ge a$ .
  - c) Tìm các điểm  $M_1$ ,  $M_2$  tương ứng thuộc các nhánh bên trái, bên phải trục tung của hypebol để  $M_1M_2$  nhỏ nhất.
- 7.37. Một cột trụ hình hypebol (H.7.36), có chiều cao 6 m, chỗ nhỏ nhất ở chính giữa và rộng 0,8 m, đỉnh cột và đáy cột đều rộng 1m. Tính độ rộng của cột ở độ cao 5 m (tính theo đơn vị mét và làm tròn tới hai chữ số sau dấu phẩy).

KẾT NỐI TRI THỰC VỚI CUỘC SỐNG 0,8 m

Hình 7.36

# CHƯƠNG VIII ĐẠI SỐ TỔ HỢP

Chương này cung cấp những kiến thức cơ bản về Đại số tổ hợp, bao gồm hai quy tắc đếm thường dùng là quy tắc cộng và quy tắc nhân; các khái niệm và công thức về hoán vị, chỉnh hợp, tổ hợp; công thức khai triển nhị thức Newton trong trường hợp số mũ thấp.

![](_page_60_Figure_2.jpeg)

Bài **23** 

# QUY TẮC ĐẾM

# THUẬT NGỮ

- Quy tắc cộng
- Quy tắc nhân
- Sơ đồ hình cây

# KIẾN THỨC, KĨ NĂNG

- Vận dụng quy tắc cộng, quy tắc nhân để tính toán số cách thực hiện một công việc hoặc đếm số phần tử của một tập hợp.
- Vận dụng sơ đồ hình cây trong các bài toán đếm đơn giản.

Đếm là một bài toán cổ xưa nhất của nhân loại. Trong khoa học và trong cuộc sống, người ta cần đếm các đối tượng để giải quyết các vấn đề khác nhau. Chẳng hạn như bài toán sau:

Mỗi mật khẩu của một trang web là một dãy có từ 2 tới 3 kí tự, trong đó kí tự đầu tiên là một trong 26 chữ cái in thường trong bảng chữ cái tiếng Anh (từ a đến z), mỗi kí tự còn lại là một chữ số từ 0 đến 9. Hỏi có thể tao được bao nhiều mật khẩu khác nhau?

Bài học này sẽ giúp em hiểu và áp dụng hai quy tắc đếm cơ bản để giải quyết bài toán trên.

# 1. QUY TẮC CỘNG VÀ SƠ ĐỔ HÌNH CÂY

Ho1. Chọn chuyến đi (H.8.1)

Từ Hà Nội vào Vinh mỗi ngày có 7 chuyến tàu hoả và 2 chuyến máy bay. Bạn An muốn ngày Chủ nhật này đi từ Hà Nội vào Vinh bằng tàu hoả hoặc máy bay.

Hỏi bạn An có bao nhiều cách chọn chuyển đi?

![](_page_61_Picture_4.jpeg)

## >> HD2. Chọn vé tàu (H.8.2)

Bạn An đã quyết định mua vé tàu đi từ Hà Nội vào Vinh trên chuyến tàu SE7. Trên tàu có các toa ghế ngồi và các toa giường nằm. Toa ngồi có hai loại vé: ngồi cứng và ngồi mềm. Toa nằm có loại khoang 4 giường và khoang 6 giường. Khoang 4 giường có hai loại vé: tầng 1 và tầng 2, khoang 6 giường có ba loại vé: tầng 1, tầng 2 và tầng 3. Hỏi:

![](_page_61_Figure_7.jpeg)

b) Có bao nhiều loại vé để bạn An lựa chọn?

![](_page_61_Figure_9.jpeg)

## Quy tắc cộng

Giả sử một công việc nào đó có thể thực hiện theo một trong hai phương án khác nhau:

- Phương án một có n<sub>1</sub> cách thực hiện,
- Phương án hai có **n**₂ cách thực hiện.

Khi đó số cách thực hiện công việc sẽ là:  $n_1 + n_2$  cách.

phương án 1 ...... n<sub>1</sub> cách

phương án 2 ..... n<sub>2</sub> cách

Chú ý. Sơ đồ minh hoạ cách phân chia trường hợp như trong Hình 8.2 được gọi là sơ đồ hình cây. Trong các bài toán đếm, người ta thường dùng sơ đồ hình cây để minh hoạ, giúp cho việc đếm thuận tiện và không bỏ sót trường hợp.

Ví dụ 1. Một quán phục vụ ăn sáng có bán phở và bún. Phở có 2 loại là phở bò và phở gà. Bún có 3 loại là bún bò, bún riêu cua và bún cá. Một khách hàng muốn chọn một món để ăn sáng. Vẽ sơ đồ hình cây minh hoạ và cho biết khách hàng đó có bao nhiêu cách lựa chọn một món ăn sáng.

Giải. Ta có sơ đồ hình cây như Hình 8.3.

Theo quy tắc cộng, số cách chọn một món ăn sáng là:

$$2 + 3 = 5$$
 (cách).

![](_page_61_Picture_22.jpeg)

Chú ý. Ta áp dụng quy tắc cộng cho một công việc có nhiều phương án khi các phương án đó phải rời nhau, không phụ thuộc vào nhau (độc lập với nhau).

- > Ví du 2. Một bộ cờ vua có 32 quân cờ như Hình 8.4.
  - a) Bạn Nam lấy ra tất cả các quân tốt. Hãy đếm xem Nam lấy ra bao nhiêu quân cờ.
  - b) Bạn Nam lấy ra tất cả các quân cờ trắng và tất cả các quân tốt. Hãy đếm số quân cờ Nam lấy ra.

### Giải

- a) Quân cờ bạn Nam lấy ra có thể thuộc hai loại: màu trắng hoặc màu đen.
- Số quân tốt trắng: 8 quân;
- Số quân tốt đen: 8 quân.

Nam lấy ra: 8 + 8 = 16 (quân cờ).

- b) Nam lấy tất cả các quân trắng và tất cả các quân tốt.
- Đầu tiên ta đếm tất cả các quân cờ trắng, có 16 quân;
- Tiếp theo ta đếm tất cả các quân tốt, có 16 quân tốt.

Vì trong 16 quân tốt có 8 quân tốt trắng đã được đếm nên số quân cờ Nam lấy ra là:

$$16 + 16 - 8 = 24$$
 (quân cờ).

Nhận xét. Ở câu b), nếu gọi A là tập hợp gồm tất cả các quân cờ trắng, B là tập hợp gồm tất cả các quân tốt thì các quân cờ Nam lấy ra chính là các phần tử của tập hợp  $A \cup B$ . Nếu ta áp dụng quy tắc cộng:  $n(A \cup B) = n(A) + n(B) = 32$  (quân cờ), suy ra Nam lấy ra 32 quân cờ. Kết luận khi đó là sai, vì  $A \cap B \neq \emptyset$  nên ta không thể áp dụng quy tắc cộng để tính trong trường hợp này.

![](_page_62_Picture_15.jpeg)

----- 8 guân

Luyện tập 1. Có bao nhiêu số tự nhiên từ 1 đến 30 mà không nguyên tố cùng nhau với 35?

Hai số tự nhiên a và b gọi là nguyên tố cùng nhau nếu chúng có ước chung lớn nhất là 1.

Hình 8.4

tốt đen

tốt trắng ----- 8 quân

# 2. QUY TẮC NHÂN

H93. Thầy Trung muốn đi từ Hà Nội vào Huế, rồi từ Huế vào Quảng Nam. Biết rằng từ Hà Nội vào Huế có thể đi bằng 3 cách: ô tô, tàu hoả hoặc máy bay. Còn từ Huế vào Quảng Nam có thể đi bằng 2 cách: ô tô hoặc tàu hoả (H.8.5).

![](_page_62_Picture_20.jpeg)

![](_page_62_Picture_21.jpeg)

Hỏi thầy Trung có bao nhiều cách chọn các phương tiện để đi từ Hà Nội vào Quảng Nam?

HĐ4. Để lắp ghế vào một phòng chiếu phim, các ghế được gắn nhãn bằng một chữ cái in hoa (trong bảng 26 chữ cái tiếng Anh từ A đến Z) đứng trước và một số nguyên từ 1 đến 20, chẳng hạn X15, Z2, ...

Hỏi có thể gắn nhãn tối đa được cho bao nhiêu ghế?

![](_page_63_Picture_2.jpeg)

Ta nhận thấy muốn làm một việc có hai công đoạn lần lượt thì trước hết ta xét xem công đoạn một có bao nhiều cách, sau đó với mỗi cách của công đoạn một, ta tính xem công đoạn hai có bao nhiều cách. Khi đó số cách thực hiện công việc tính theo quy tắc sau:

## Quy tắc nhân

Giả sử một công việc nào đó phải hoàn thành qua hai công đoạn liên tiếp nhau:

- Công đoạn một có m₁ cách thực hiện,
- Với mỗi cách thực hiện công đoạn một, có  $m_2$  cách thực hiện công đoạn hai.

Khi đó số cách thực hiện công việc là:  $m_1 \cdot m_2$  cách.

## Chúý

Quy tắc nhân áp dụng để tính số cách thực hiện một công việc có nhiều công đoạn, các công đoạn nối tiếp nhau và những công đoạn này độc lập với nhau.

Ví dụ 3. Một người muốn mua vé tàu ngồi đi từ Hà Nội vào Vinh. Có ba chuyến tàu là SE5, SE7 và SE35. Trên mỗi tàu có 2 loại vé ngồi khác nhau: ngồi cứng hoặc ngồi mềm. Hỏi có bao nhiêu loại vé ngồi khác nhau để người đó lựa chọn?

#### Giải

Để mua được vé tàu, người đó phải thực hiện hai công đoạn:

## Chọn chuyển tàu --> Chọn loại vé

Có 3 cách chọn chuyến tàu, với mỗi chuyến tàu có 2 cách chọn loại vé ngồi. Áp dụng quy tắc nhân, ta có số cách chọn loại vé là:  $3 \cdot 2 = 6$  (cách).

Chú ý. Ta cũng có thể dùng quy tắc cộng. Người mua vé có thể lựa chọn một trong ba trường hợp: SE5, SE7 hoặc SE35.

Nếu lựa chọn SE5, có hai loại vé: loại vé SE5 ngồi cứng và SE5 ngồi mềm. Tương tự cho trường hợp SE7 và trường hợp SE35.

Mỗi trường hợp có hai loại vé. Tổng cộng có:

2 + 2 + 2 = 6 (cách chọn loại vé).

![](_page_63_Picture_20.jpeg)

![](_page_63_Picture_21.jpeg)

**Luyện tập 2.** Tại kì World Cup năm 2018, vòng bảng gồm có 32 đội tham gia, được chia vào 8 bảng, mỗi bảng 4 đội thi đấu vòng tròn (mỗi đội chơi một trận với từng đội khác trong cùng bảng). Hỏi tổng cộng vòng bảng có bao nhiêu trận đấu?

# 3. KẾT HỢP QUY TẮC CỘNG VÀ QUY TẮC NHÂN

Trong các ví dụ trước, chúng ta chỉ cần áp dụng một quy tắc đếm. Tuy nhiên, hầu hết các bài toán đếm trong thực tế sẽ phức tạp hơn và thường phải áp dụng cả hai quy tắc.

Ví dụ 4. Để tổ chức bữa tiệc, người ta chọn thực đơn gồm một món khai vị, một món chính và một món tráng miệng. Nhà hàng đưa ra danh sách: khai vị có 2 loại súp và 3 loại sa lát; món chính có 4 loại thịt, 3 loại cá và 3 loại tôm; tráng miệng có 5 loại kem và 3 loại bánh. Hỏi có thể thiết kế bao nhiều thực đơn khác nhau?

#### Giải

Để chọn thực đơn, ta chia thành 3 công đoạn chọn món.

Công đoạn 1, chọn món khai vị: vì có hai phương án là súp hoặc sa lát nên ta áp dụng quy tắc cộng. Số cách chọn là: 2+3=5 (cách).

Chọn món khai vị

Chọn món chính

Chon món tráng miệng

Công đoạn 2, chọn món chính: tương tự, ta có số cách chọn là:

4 + 3 + 3 = 10 (cách).

Công đoạn 3, chọn món tráng miệng: tương tự, ta có số cách chọn là: 5 + 3 = 8 (cách).

Tổng kết, theo quy tắc nhân, số cách chọn thực đơn là: 5 · 10 · 8 = 400 (cách).

Chú ý. Quy tắc cộng được áp dụng khi công việc được chia thành các phương án phân biệt (thực hiện một trong các phương án để hoàn thành công việc).

Quy tắc nhân được áp dụng khi công việc có nhiều công đoạn nối tiếp nhau (phải thực hiện tất cả các công đoạn để hoàn thành công việc).

- >>> Luyện tập 3. Từ các chữ số 0, 1, 2, 3 có thể lập được bao nhiêu số thoả mãn:
  - a) Là số tự nhiên có ba chữ số khác nhau?
  - b) Là số tự nhiên chẵn có ba chữ số khác nhau?
- >> Ví dụ 5. Trở lại *tình huống mở đầu*, ta thấy có hai trường hợp: độ dài của mật khẩu là 2 hoặc 3 kí tự.
  - Trường hợp 1: độ dài mật khẩu là 2 kí tự. Chọn từng kí tự và áp dụng quy tắc nhân.
     Kí tự đầu tiên có 26 cách chọn trong các chữ cái in thường tiếng Anh.
    - Kí tự thứ hai có 10 cách chọn trong các chữ số từ 0 đến 9.
    - Vậy, theo quy tắc nhân, ta có 26·10 = 260 cách chọn mật khẩu trong trường hợp 1.
  - Trường hợp 2: độ dài mật khẩu là 3 kí tự.
     Tương tự như trường hợp 1, ta có 26·10² = 2 600 cách chọn mật khẩu.

Vì có hai trường hợp rời nhau, mật khẩu có thể rơi vào một trong hai trường hợp, nên ta áp dung guy tắc công. Tổng số mật khẩu có thể là 260 + 2 600 = 2 860.

**>> Vận dụng.** Khối lớp 10 của một trường trung học phổ thông có ba lớp 10A, 10B, 10C. Lớp 10A có 30 ban, lớp 10B có 35 ban, lớp 10C có 32 ban. Nhà trường muốn chon 4 ban để thành lập đôi cờ đỏ của khối sao cho có đủ đại diện của các lớp. Hỏi có bao nhiều cách lua chon?

## **BÀI TÂP**

- 8.1. Trên giá sách có 8 cuốn truyên ngắn, 7 cuốn tiểu thuyết và 5 tập thơ (tất cả đều khác nhau). Vẽ sơ đồ hình cây minh hoa và cho biết ban Phong có bao nhiều cách chon một cuốn để đọc vào ngày cuối tuần.
- 8.2. Một người gieo đồng xu hai mặt, sau mỗi lần gieo thì ghi lại kết quả là sấp hay ngửa. Hỏi nếu người đó gieo 3 lần thì có thể có bao nhiều khả năng xảy ra?
- 8.3. Ở một loài thực vật, A là gen trội quy định tính trạng hoa kép, a là gen lặn quy định tính trang hoa đơn.
  - a) Sự tổ hợp giữa hai gen trên tạo ra mấy kiểu gen? Viết các kiểu gen đó.
  - b) Khi giao phối ngẫu nhiên, có bao nhiêu kiểu giao phối khác nhau từ các kiểu gen đó?
- 8.4. Có bao nhiêu số tư nhiên
  - a) có 3 chữ số khác nhau?
  - b) là số lẻ có 3 chữ số khác nhau?
  - c) là số có 3 chữ số và chia hết cho 5?
  - d) là số có 3 chữ số khác nhau và chia hết cho 5?
- 8.5. a) Mật khẩu của chương trình máy tính quy định gồm 3 kí tự, mỗi kí tự là một chữ số. Hỏi có thể tạo được bao nhiều mật khẩu khác nhau?
  - b) Nếu chương trình máy tính quy định mới mật khẩu vẫn gồm 3 kí tự, nhưng kí tự đầu tiên phải là một chữ cái in hoa trong bảng chữ cái tiếng Anh gồm 26 chữ (từ A đến Z) và 2 kí tự sau là các chữ số (từ 0 đến 9). Hỏi quy định mới có thể tạo được nhiều hơn quy định cũ bao nhiệu mật khẩu khác nhau?

# <sup>Bài</sup> **24**

# HOÁN VỊ, CHỈNH HỢP VÀ TỔ HƠP

## THUẬT NGỮ

- Hoán vi
- · Chỉnh hợp
- Tổ hợp

# KIẾN THỨC, KĨ NĂNG

- Tính số hoán vị, chỉnh hợp, tổ hợp.
- Tính số hoán vị, chỉnh hợp, tổ hợp bằng máy tính cầm tay.

Danh sách các cầu thủ của Đội tuyển bóng đá quốc gia tham dự một trận đấu quốc tế có 23 cầu thủ gồm 3 thủ môn, 7 hậu vệ, 8 tiền vệ và 5 tiền đạo. Huấn luyện viên rất bí mật, không cho ai biết đội hình (danh sách 11 cầu thủ) sẽ ra sân. Trong cuộc họp báo, ông chỉ tiết lộ đội sẽ đá theo sơ đồ 3 – 4 – 3 (nghĩa là 3 hậu vệ, 4 tiền vệ, 3 tiền đạo và 1 thủ môn). Đối thủ đã có danh sách 23 cầu thủ (tên và vi trí của từng

![](_page_66_Picture_10.jpeg)

cầu thủ) và rất muốn dự đoán đội hình, họ xét hết các khả năng có thể xảy ra. Hỏi nếu đối thủ đã dự đoán được trước vị trí thủ môn thì họ sẽ phải xét bao nhiêu đội hình có thể?

## 1. HOÁN VỊ

H91. Một nhóm gồm bốn bạn Hà, Mai, Nam, Đạt xếp thành một hàng, từ trái sang phải, để tham gia một cuộc phỏng vấn.

![](_page_66_Picture_14.jpeg)

![](_page_66_Picture_16.jpeg)

![](_page_66_Picture_17.jpeg)

Hà

Mai

Nam

Đat

- a) Hãy liệt kê ba cách sắp xếp bốn bạn trên theo thứ tự.
- b) Có bao nhiêu cách sắp xếp thứ tự bốn bạn trên để tham gia phỏng vấn?

Nhận xét. Mỗi cách sắp xếp thứ tự của bốn bạn tham gia phỏng vấn ở HĐ1 được gọi là một hoán vị của tập hợp gồm bốn bạn này. Số các hoán vị của bốn bạn ở HĐ1 là 4 · 3 · 2 · 1.

## Tổng quát ta có

Một hoán vị của một tập hợp có n phần tử là một cách sắp xếp có thứ tự n phần tử đó (với n là một số tự nhiên,  $n \ge 1$ ).

Số các hoán vị của tập hợp có n phần tử, kí hiệu là  $P_n$ , được tính bằng công thức

$$P_n = n \cdot (n-1) \cdot (n-2) \cdot \cdot \cdot \cdot 2 \cdot 1.$$

Chú ý. Kí hiệu  $n \cdot (n-1) \cdot (n-2) \cdot \cdots \cdot 2 \cdot 1$  là n! (đọc là n giai thừa), ta có:  $P_n = n!$ . Chẳng hạn  $P_3 = 3! = 3 \cdot 2 \cdot 1 = 6$ .

Quy ước 0! = 1.

Ví dụ 1. Từ các chữ số 6, 7, 8 và 9 có thể lập được bao nhiều số có bốn chữ số khác nhau?
Giải

Mỗi cách sắp xếp bốn chữ số đã cho để lập thành một số có bốn chữ số khác nhau là một hoán vi của bốn chữ số đó.

Vậy số các số có bốn chữ số khác nhau có thể lập được là  $P_4 = 4! = 24$ .

Luyện tập 1. Trong một cuộc thi điền kinh gồm 6 vận động viên chạy trên 6 đường chạy. Hỏi có bao nhiêu cách xếp các vận động viên vào các đường chạy đó?

# 2. CHỈNH HỢP

- HĐ2. Trong lớp 10T có bốn bạn Tuấn, Hương, Việt, Dung đủ tiêu chuẩn tham gia cuộc thi hùng biện của trường.
  - a) Giáo viên cần chọn ra hai bạn phụ trách nhóm trên. Hỏi có bao nhiêu cách chọn hai bạn từ bốn bạn nêu trên?
  - b) Có bao nhiêu cách chọn hai bạn, trong đó một bạn làm nhóm trưởng, một bạn làm nhóm phó?

Nhận xét. Trong HĐ2b, mỗi cách sắp xếp hai bạn từ bốn bạn làm nhóm trưởng, nhóm phó được gọi là một *chỉnh hợp* chập 2 của 4. Để tính số các chỉnh hợp ta dùng quy tắc nhân. Tổng quát ta có:

Một chỉnh hợp chập k của n là một cách sắp xếp có thứ tự k phần tử từ một tập hợp n phần tử (với k, n là các số tự nhiên,  $1 \le k \le n$ ).

Số các chỉnh hợp chập k của n, kí hiệu là  $A_n^k$ , được tính bằng công thức

$$A_n^k = n \cdot (n-1) \cdots (n-k+1) \text{ hay } A_n^k = \frac{n!}{(n-k)!} (1 \le k \le n).$$

>> Ví dụ 2. Một lớp có 30 học sinh, giáo viên cần chọn lần lượt 4 học sinh trồng bốn cây khác nhau để tham gia lễ phát động Tết trồng cây của trường. Hỏi giáo viên có bao nhiêu cách chọn?

#### Giải

Mỗi cách chọn lần lượt 4 trong 30 học sinh để trồng bốn cây khác nhau là một chỉnh hợp chập 4 của 30.

Vậy số cách chọn là  $A_{30}^4 = 657720$ .

Chú ý

- Hoán vị sắp xếp tất cả các phần tử của tập hợp, còn chỉnh hợp chọn ra một số phần tử và sắp xếp chúng.
- Mỗi hoán vị của n phần tử cũng chính là một chỉnh hợp chập n của n phần tử đó. Vì vậy P<sub>n</sub> = A<sub>n</sub><sup>n</sup>.

Ngày 28-11-1959, Chủ tịch Hồ Chí Minh đã phát động ngày "Tết trồng cây" với mong muốn: Trong mười năm, đất nước ta phong cảnh sẽ ngày càng tươi đẹp hơn, khí hậu điều hoà hơn....

![](_page_68_Picture_7.jpeg)

Luyện tập 2. Trong một giải đua ngựa gồm 12 con ngựa, người ta chỉ quan tâm đến 3 con ngựa: con nhanh nhất, nhanh nhì và nhanh thứ ba. Hỏi có bao nhiêu kết quả có thể xảy ra?

# 3. TỔ HỢP

- 🤰 ноз. Trở lại HĐ2.
  - a) Hãy cho biết sự khác biệt khi chọn ra hai bạn ở câu HĐ2a và HĐ2b.
  - b) Từ kết quả tính được ở câu HĐ2b (áp dụng chỉnh hợp), hãy chỉ ra cách tính kết quả ở câu HĐ2a.

## Nhận xét

Mỗi cách chọn ra 2 bạn từ 4 bạn ở HĐ2a được gọi là một *tổ hợp* chập 2 của 4. Vì không cần sắp xếp thứ tự hai bạn được chọn nên số cách chọn sẽ giảm đi 2! lần so với việc chọn ra hai bạn có sắp xếp thứ tự (ở câu HĐ2b).

Tổng quát ta có:

Một tổ hợp chập k của n là một cách chọn k phần tử từ một tập hợp n phần tử (với k, n là các số tự nhiên,  $0 \le k \le n$ ).

Số các tổ hợp chập k của n, kí hiệu là  $C_n^k$ , được tính bằng công thức

$$C_n^k = \frac{n!}{(n-k)!k!} (0 \le k \le n).$$

## Chú ý

- $C_n^k = \frac{A_n^k}{k!}$
- Chỉnh hợp và tổ hợp có điểm giống nhau là đều chọn một số phần tử trong một tập hợp, nhưng khác nhau ở chỗ, chỉnh hợp là chọn có xếp thứ tự, còn tổ hợp là chọn không xếp thứ tư.
- Ví dụ 3. Có 7 bạn học sinh muốn chơi cờ cá ngựa, nhưng mỗi ván chỉ có 4 người chơi. Hỏi có bao nhiêu cách chọn 4 bạn chơi cờ cá ngựa?

### Giải

Mỗi cách chọn 4 bạn trong 7 bạn học sinh là một tổ hợp chập 4 của 7.

Vậy số cách chọn 4 bạn chơi cờ cá ngựa là  $C_7^4 = \frac{7!}{4!3!} = 35$ .

Luyện tập 3. Trong ngân hàng đề kiểm tra cuối học kì II môn Vật lí có 20 câu lí thuyết và 40 câu bài tập. Người ta chọn ra 2 câu lí thuyết và 3 câu bài tập trong ngân hàng đề để tạo thành một đề thi. Hỏi có bao nhiêu cách lập đề thi gồm 5 câu hỏi theo cách chọn như trên?

# 4. ỨNG DỤNG HOÁN VỊ, CHỈNH HỢP, TỔ HỢP VÀO CÁC BÀI TOÁN ĐẾM

Các khái niệm hoán vị, chỉnh hợp và tổ hợp liên quan mật thiết với nhau và là những khái niệm cốt lõi của các phép đếm. Rất nhiều bài toán đếm liên quan đến việc lựa chọn, việc sắp xếp, vì vậy các công thức tính  $P_n$ ,  $A_n^k$ ,  $C_n^k$  sẽ được dùng rất nhiều.

Dưới đây ta xét một số ví dụ về các bài toán đếm.

- Ví dụ 4. Một lần anh Hưng đến Hà Nội và dự định từ Hà Nội tham quan Đền Hùng, Ninh Bình, Hạ Long, Đường Lâm và Bát Tràng, mỗi ngày đi tham quan một địa điểm rồi lại về Hà Nội.
  - a) Hỏi anh Hưng có thể xếp được bao nhiêu lịch trình đi tham quan tất cả các địa điểm (ở đây lịch trình tính cả thứ tự tham quan).
  - b) Anh Hưng có việc đột xuất phải về sớm, nên anh chỉ có 3 ngày để đi tham quan 3 địa điểm. Hỏi anh Hưng có bao nhiều cách xếp lịch trình đi tham quan?

### Giải

a) Anh Hưng đi tham quan 5 địa điểm, mỗi cách xếp lịch trình là một cách chọn có thứ tự của 5 địa điểm trên. Vậy số cách xếp lịch trình chính bằng số các hoán vị của 5 địa điểm, và bằng

$$P_5 = 5! = 5 \cdot 4 \cdot 3 \cdot 2 \cdot 1 = 120$$
 (cách).

b) Nếu anh Hưng chỉ có 3 ngày để đi tham quan 3 nơi, thì mỗi cách xếp lịch trình của anh chính là một cách chọn có thứ tự 3 địa điểm từ 5 địa điểm, tức là một chỉnh hợp chập 3 của 5.

Vậy số cách xếp lịch trình đi tham quan trong trường hợp này là

$$A_5^3 = \frac{5!}{(5-3)!} = \frac{5!}{2!} = 60$$
 (cách).

>> Ví dụ 5. Giải bài toán trong *tình huống mở đầu* về đội hình của Đội tuyển bóng đá quốc gia.

### Giải

Vì mỗi đội hình gồm có 1 thủ môn, 3 hậu vệ, 4 tiền vệ và 3 tiền đạo và đã biết trước vị trí thủ môn, nên để chọn đội hình ta cần thực hiện 3 công đoạn:

![](_page_69_Picture_19.jpeg)

- 1. Chọn hậu vệ là chọn 3 trong số 7 hậu vệ: có  $C_7^3 = 35$  (cách).
- 2. Chọn tiền vệ là chọn 4 trong số 8 tiền vệ: có  $C_8^4 = 70$  (cách).
- 3. Chọn tiền đạo là chọn 3 trong số 5 tiền đạo: có  $C_5^3 = 10$  (cách).

Vậy, theo quy tắc nhân, số các đội hình có thể có (khi đã biết vị trí thủ môn) là 35.70.10 = 24500.

- >> Vân dung. Một câu lạc bộ có 20 học sinh.
  - a) Có bao nhiêu cách chon 6 thành viên vào Ban quản lí?
  - b) Có bao nhiều cách chọn Trưởng ban, 1 Phó ban, 4 thành viên khác vào Ban quản lí?

# 5. SỬ DUNG MÁY TÍNH CẨM TAY

Ta có thể dùng máy tính cầm tay để tính số các hoán vị, chỉnh hợp và tổ hợp.

## Hoán vi

Để tính n!, ta ấn phím theo trình tự sau:

Án số n, ấn phím 💷 🗷, sau đó ấn phím 🖃 . Khi đó, kết quả sẽ hiển thị ở dòng kết quả.

Ví du. Tính 9!

Ta ấn liên tiếp các phím như sau: 9 sur x =

Dòng kết quả hiện ra 362 880.

## Chinh hop

Để tính  $A_n^k$  ta ấn phím theo trình tự sau:

Án số n, ấn phím  $\mathbf{SHF}$   $\mathbf{X}$ , ấn số k, sau đó ấn phím  $\mathbf{\Xi}$ . Khi đó, kết quả sẽ hiển thị ở dòng kết quả.

 $Vi d\mu$ . Tinh  $A_{15}^2$ .

Ta ấn các phím theo trình tự sau: 1 5 💵 🗙 2 🖃

Dòng kết quả hiện ra 210.

### Tổ hợp

Để tính  $C_n^k$  ta ấn phím theo trình tự sau:

Án số n, ấn phím 🖭 🔁 , ấn số k, sau đó ấn phím  $\sqsubseteq$  . Khi đó, kết quả sẽ hiển thị ở dòng kết quả. I CUỐC SỐNG

 $Vi d\mu$ . Tinh  $C_{20}^5$ .

Ta ấn các phím theo trình tự sau: ② ① 💵 🛨 5 🖃

Dòng kết quả hiện ra 15 504.

## **BÀI TÂP**

- 8.6. Một hoạ sĩ cần trưng bày 10 bức tranh nghệ thuật khác nhau thành một hàng ngang. Hỏi có bao nhiêu cách để hoạ sĩ sắp xếp các bức tranh?
- 8.7. Từ các chữ số 0, 1, 2, 3, 4 có thể lập được bao nhiêu số tự nhiên có ba chữ số khác nhau?
- 8.8. Có bao nhiêu cách chọn một tập hợp gồm hai số nguyên dương nhỏ hơn 100? Có bao nhiêu cách chọn một tập hợp gồm ba số nguyên dương nhỏ hơn 100?
- 8.9. Bạn Hà có 5 viên bị xanh và 7 viên bị đỏ. Có bao nhiều cách để Hà chọn ra đúng 2 viên bi khác màu?

- 8.10. Một câu lạc bộ cờ vua có 10 bạn nam và 7 bạn nữ. Huấn luyện viên muốn chọn 4 bạn đi thi đấu cờ vua.
  - a) Có bao nhiêu cách chọn 4 bạn nam?
  - b) Có bao nhiều cách chọn 4 bạn không phân biệt nam, nữ?
  - c) Có bao nhiều cách chọn 4 bạn, trong đó có 2 bạn nam và 2 bạn nữ?
- 8.11. Có bao nhiêu số tư nhiên chia hết cho 5 mà mỗi số có bốn chữ số khác nhau?

### Em có biết?

• Có thể coi người đầu tiên đưa các bài toán tổ hợp vào châu Âu là Leonardo Fibonacci ở thành Pisa (thuộc nước Italia ngày nay) vào thế kỉ XIII. Trong cuốn sách *Liber Abaci (Sách tính)*, ông đã giới thiệu dãy số Fibonacci: F<sub>0</sub> = 0,F<sub>1</sub> = 1,F<sub>2</sub> = 1,F<sub>3</sub> = 2,F<sub>4</sub> = 3,F<sub>5</sub> = 5,... Trong dãy số này, kể từ số hạng thứ ba trở đi, mỗi số hạng bằng tổng của hai số hạng đứng ngay trước nó, tức là F<sub>n+1</sub> = F<sub>n</sub> + F<sub>n-1</sub>. Bằng các lập luận tổ hợp, có thể chứng minh được rằng tổng số các cách khác nhau để xếp được một hình chữ nhật có kích thước 1 × n từ hai loại gạch có kích thước 1 × 1 và 1 × 2 chính là F<sub>n+1</sub>. Sử dụng tính chất này, ta có hằng đẳng thức

![](_page_71_Picture_7.jpeg)

Fibonacci (1170 - 1250)

$$F_{n+1} = \sum_{k+m=n} C_m^k,$$

trong đó vế phải là tổng của tất cả các số  $C_m^k$  với k + m = n.

 Câu hỏi một ván cờ vua có thể có nhiều nhất bao nhiêu nước đi có vẻ rất phức tạp vì mỗi ván một vẻ. Vậy mà bằng các tính toán tổ hợp, người ta đã chứng minh rằng về lí thuyết, một ván cờ có tối đa 5 950 nước đi.

# VỚI CUỘC SỐNG

Bài 25

# **NHỊ THỰC NEWTON**

## THUẬT NGỮ

- Khai triển
- Nhi thức

# KIẾN THỨC, KĨ NĂNG

 Khai triển nhị thức Newton (a + b)<sup>n</sup> bằng ∨ận dụng tổ hợp với số mũ thấp (n = 4 hoặc n = 5).

Ở lớp 8, khi học về hằng đẳng thức, ta đã biết khai triển:

$$(a + b)^2 = a^2 + 2ab + b^2;$$

$$(a + b)^3 = a^3 + 3a^2b + 3ab^2 + b^3$$
.

Quan sát các đơn thức ở vế phải của các đẳng thức trên, hãy nhận xét về quy luật số mũ của a và b. Có thể tìm được cách tính các hệ số của đơn thức trong khai triển  $(a+b)^n$  khi  $n \in \{4, 5\}$  không?

- **)** H91. Hãy xây dựng sơ đồ hình cây của tích hai nhị thức  $(a + b) \cdot (c + d)$  như sau:
  - Từ một điểm gốc, kẻ các mũi tên, mỗi mũi tên tương ứng với một đơn thức (gọi là nhãn của mũi tên) của nhị thức thứ nhất (H.8.6);
  - Từ ngọn của mỗi mũi tên đã xây dựng, kẻ các mũi tên, mỗi mũi tên tương ứng với một đơn thức của nhi thức thứ hai;
  - Tại ngọn của các mũi tên xây dựng tại bước sau cùng, ghi lại tích của các nhãn của các mũi tên đi từ điểm gốc đến đầu mút đó.

Hãy lấy tổng của các tích nhận được và so sánh kết quả với khai triển của tích  $(a + b) \cdot (c + d)$ .

HĐ2. Hãy cho biết các đơn thức còn thiếu (...) trong sơ đồ hình cây (H.8.7) của tích (a + b)·(a + b)·(a + b).

Có bao nhiều tích nhận được lần lượt bằng  $a^3$ ,  $a^2b$ ,  $ab^2$ ,  $b^3$ ?

Hãy so sánh chúng với các hệ số nhận được khi khai triển  $(a + b)^3$ .

Sơ đồ hình cây của  $(a + b) \cdot (c + d)$ 

![](_page_72_Figure_20.jpeg)

Hình 8.6

Sơ đồ hình cây của  $(a + b) \cdot (a + b) \cdot (a + b)$ .

![](_page_72_Figure_23.jpeg)

Hình 8.7

Nhận xét. Các tích nhận được từ sơ đồ hình cây của một tích các đa thức giống như cách lấy ra một đơn thức từ mỗi đa thức rồi nhân lại với nhau. Hơn nữa, tổng của chúng cho ta khai triển của tích các đa thức đã cho.

Chẳng hạn, trong sơ đồ hình cây (H.8.8) của  $(a + b) \cdot (c + d)$  thì các tích nhận được là  $a \cdot c$ ,  $a \cdot d$ ,  $b \cdot c$ ,  $b \cdot d$  cũng chính là các tích nhận được khi ta lấy một hạng tử của nhị thức thứ nhất (là a hoặc b) nhân với một hạng tử của nhị thức thứ hai (là c hoặc d). Ta có

$$(a+b)\cdot(c+d)=a\cdot c+a\cdot d+b\cdot c+b\cdot d.$$

![](_page_73_Picture_3.jpeg)

H93. Hãy vẽ sơ đồ hình cây của khai triển (a + b)⁴ được mô tả như Hình 8.9. Sau khi khai triển, ta thu được một tổng gồm 2⁴ (theo quy tắc nhân) đơn thức có dạng x · y · z · t , trong đó mỗi x, y, z, t là a hoặc b. Chẳng hạn, nếu x, y, t là a, còn z là b thì ta có đơn thức a · a · b · a, thu gọn là a³b. Để có đơn thức này, thì trong 4 nhân tử x, y, z, t có 1 nhân tử là b, 3 nhân tử còn lại là a. Khi đó số đơn thức đồng dạng với a³b trong tổng là C⁴.

Sơ đồ hình cây của  $(a + b)^4$ 

![](_page_73_Figure_6.jpeg)

Lập luận tương tự trên, dùng kiến thức về tổ hợp, hãy cho biết trong tổng nêu trên, có bao nhiêu đơn thức đồng dạng với mỗi đơn thức thu gọn sau:

• 
$$a^4$$
; •  $a^3b$ ; •  $a^2b^2$ ; •  $ab^3$ ; •  $b^4$ ?

Từ HĐ3, sau khi rút gọn các đơn thức đồng dạng ta thu được:

$$(a+b)^4 = C_4^0 a^4 + C_4^1 a^3 b + C_4^2 a^2 b^2 + C_4^3 a b^3 + C_4^4 b^4$$
$$= a^4 + 4a^3 b + 6a^2 b^2 + 4ab^3 + b^4.$$

Trong khai triển nhị thức Newton (a + b)⁴, các đơn thức có bậc là 4.

**) Ví dụ 1.** Khai triển (2x + 1)<sup>4</sup>.

#### Giai

Thay a = 2x và b = 1 trong công thức khai triển của  $(a + b)^4$ , ta được:

$$(2x + 1)^4 = (2x)^4 + 4 \cdot (2x)^3 \cdot 1 + 6 \cdot (2x)^2 \cdot 1^2 + 4 \cdot (2x) \cdot 1^3 + 1^4$$
$$= 16x^4 + 32x^3 + 24x^2 + 8x + 1.$$

**Luyện tập 1.** Khai triển  $(x-2)^4$ .

![](_page_73_Picture_17.jpeg)

**>> HD4.** Tương tư như HĐ3, sau khi khai triển (a + b)<sup>5</sup>, ta thu được một tổng gồm 2<sup>5</sup> đơn thức có dang  $x \cdot y \cdot z \cdot t \cdot u$ , trong đó mỗi kí hiệu x, y, z, t, u là a hoặc b. Chẳng hạn, nếu x, z là a, còn y, t, u là b thì ta có đơn thức  $a \cdot b \cdot a \cdot b \cdot b$ , thu gọn là  $a^2b^3$ . Để có đơn thức này, thì trong 5 nhân tử x, y, z, t, u có 3 nhân tử là b, 2 nhân tử còn lai là a. Khi đó số đơn thức đồng dang với  $a^2b^3$  trong tổng là  $C_5^3$ .

Lập luận tương tư như trên, dùng kiến thức về tổ hợp, hãy cho biết, trong tổng nhận được nêu trên có bao nhiêu đơn thức đồng dạng với mỗi đơn thức thu gọn sau:

· b5?

• a<sup>2</sup>b<sup>3</sup> • ab<sup>4</sup>

$$(a+b)^5 = C_5^0 a^5 + C_5^1 a^4 b + C_5^2 a^3 b^2 + C_5^3 a^2 b^3 + C_5^4 a b^4 + C_5^5 b^5$$
  
=  $a^5 + 5a^4 b + 10a^3 b^2 + 10a^2 b^3 + 5ab^4 + b^5$ .

Từ HĐ4, sau khi rút gọn các đơn thức đồng dạng ta thu được:

Trong khai triển nhị thức Newton (a + b)5, các đơn thức có bậc là 5.

Ví du 2. Khai triến (x + 3)⁵.

Thay  $a = x \lor a$  b = 3 trong công thức khai triển của  $(a + b)^5$ , ta được:

$$(x+3)^5 = x^5 + 5 \cdot x^4 \cdot 3 + 10 \cdot x^3 \cdot 3^2 + 10 \cdot x^2 \cdot 3^3 + 5 \cdot x \cdot 3^4 + 3^5$$
$$= x^5 + 15x^4 + 90x^3 + 270x^2 + 405x + 243.$$

Luyện tập 2. Khai triển (3x – 2)5.

Nhận xét. Các công thức khai triển  $(a + b)^n$  với  $n \in \{4, 5\}$ , là một công cụ hiệu quả để tính chính xác hoặc xấp xỉ một số đại lượng mà không cần dùng máy tính.

VỚI CUỐC SỐNG

## Vận dụng

- a) Dùng hai số hạng đầu tiên trong khai triển của (1 + 0,05)⁴ để tính giá trị gần đúng của 1,05⁴.
- b) Dùng máy tính cầm tay tính giá trị của 1,054 và tính sai số tuyệt đối của giá trị gần đúng nhận được ở câu a.

# **BÀI TÂP**

8.12. Khai triển các đa thức:

a) 
$$(x - 3)^4$$
;

b) 
$$(3x - 2y)^4$$
;

c) 
$$(x + 5)^4 + (x - 5)^4$$
; d)  $(x - 2y)^5$ .

d) 
$$(x - 2y)^5$$

- 8.13. Tìm hệ số của x⁴ trong khai triển của (3x 1)⁵.
- **8.14.** Biểu diễn  $(3+\sqrt{2})^5-(3-\sqrt{2})^5$  dưới dạng  $a+b\sqrt{2}$  với a, b là các số nguyên.

- 8.15. a) Dùng hai số hạng đầu tiên trong khai triển của  $(1+0,02)^5$  để tính giá trị gần đúng của  $1,02^5$ .
  - b) Dùng máy tính cầm tay tính giá trị của 1,02⁵ và tính sai số tuyệt đối của giá trị gần đúng nhân được ở câu a.
- **8.16.** Số dân của một tỉnh ở thời điểm hiện tại là khoảng 800 nghìn người. Giả sử rằng tỉ lệ tăng dân số hằng năm của tỉnh đó là r%.
  - a) Viết công thức tính số dân của tỉnh đó sau 1 năm, sau 2 năm. Từ đó suy ra công thức tính số dân của tỉnh đó sau 5 năm nữa là  $P = 800 \left(1 + \frac{r}{100}\right)^5$  (nghìn người).
  - b) Với r = 1,5%, dùng hai số hạng đầu trong khai triển của  $(1+0,015)^5$ , hãy ước tính số dân của tỉnh đó sau 5 năm nữa (theo đơn vị nghìn người).

## Em có biết?

Trong di truyền học quần thể, nguyên lí Hardy – Weinberg đưa ra công thức toán học tính tần số của các kiểu gen trong một quần thể (thoả mãn một số điều kiện) ở các thế hệ. Trong trường hợp ở mỗi vị trí trên nhiễm sắc thể chỉ có hai alen (là một trạng thái cụ thể của một gen) A và B với các tần số khởi đầu lần lượt là p và q (p+q=1, tức là 100%), công thức của Hardy – Weinberg là tương ứng với khai triển nhị thức Newton. Chẳng hạn:

• Tần số các kiểu gen AA, AB, BB tương ứng là p², 2pq, q²

(ứng với quy tắc kết hợp  $(pA+qB)\times(pA+qB)=(pA+qB)^2=p^2AA+2pqAB+q^2BB)$ ;

- Tần số các kiểu gen AAA, AAB, ABB, BBB tương ứng là  $p^3$ ,  $3p^2q$ ,  $3pq^2$ ,  $q^3$  (ứng với  $(pA+qB)^3 = p^3AAA + 3p^2qAAB + 3pq^2ABB + q^3BBB$ );
  - Tần số các kiểu gen AAAA, AAAB, ABBB, BBBB tương ứng là

$$p^4$$
,  $4p^3q$ ,  $6p^2q^2$ ,  $4pq^3$ ,  $q^4$ 

(ứng với  $(pA + qB)^4 = C_4^0 p^4 AAAA + C_4^1 p^3 qAAAB + C_4^2 p^2 q^2 AABB + C_4^3 p q^3 ABBB + C_4^4 q^4 BBBB$ );

• Tổng quát, ta có tần số kiểu gen gồm i alen A và j alen B là  $C_{i+j}^{\ j} p^i q^j$ .

(Theo Sinh học 12, Nhà xuất bản Giáo dục Việt Nam, 2017)

# BÀI TẬP CUỐI CHƯƠNG VIII

## A - TRẮC NGHIỆM

| 8.17. | Số cách cắm | 4 bông hoa kh | ác nhau vào | 4 bình ho | oa khác nhau | (mỗi bông | hoa cắm | vàc |
|-------|-------------|---------------|-------------|-----------|--------------|-----------|---------|-----|
| m     | ột bình) là |               |             |           |              |           |         |     |

A. 16.

B. 24.

C. 8.

D. 4.

8.18. Số các số có ba chữ số khác nhau, trong đó các chữ số đều lớn hơn 0 và nhỏ hơn hoặc bằng 5 là

A. 120.

B. 60.

C. 720.

D. 2.

8.19. Số cách chọn 3 bạn học sinh đi học bơi từ một nhóm 10 bạn học sinh là

A. 3 628 800.

B. 604 800.

C. 120.

D. 720.

8.20. Bạn An gieo một con xúc xắc hai lần. Số các trường hợp để tổng số chấm xuất hiện trên con xúc xắc bằng 8 qua hai lần gieo là

A. 36.

B. 6.

C. 5.

D. 4.

8.21. Hệ số của x⁴ trong khai triển nhị thức (3x – 4)⁵ là

A. 1620.

B. 60.

C. -60.

D. -1 620.

## B - TƯ LUÂN

- 8.22. a) Có bao nhiêu cách viết một dãy 5 chữ cái in hoa từ bảng chữ cái tiếng Anh (gồm 26 chữ cái)?
  - b) Có bao nhiều cách viết một dãy 5 chữ cái in hoa khác nhau từ bảng chữ cái tiếng Anh (gồm 26 chữ cái)?
- 8.23. Từ các chữ số: 1; 2; 3; 4; 5; 6.
  - a) Có thể lập được bao nhiêu số có ba chữ số khác nhau?
  - b) Có thể lập được bao nhiêu số có ba chữ số khác nhau và chia hết cho 3?
- **8.24.** Tế bào A có 2n = 8 nhiễm sắc thể (NST), và nguyên phân 5 lần liên tiếp. Tế bào B có 2n = 14 NST và nguyên phân 4 lần liên tiếp. Tính và so sánh tổng số NST trong tế bào A và trong tế bào B được tạo ra.
- **8.25.** Lớp 10B có 40 học sinh gồm 25 nam và 15 nữ. Hỏi có bao nhiều cách chọn 3 bạn tham gia vào đội thiện nguyện của trường trong mỗi trường hợp sau?
  - a) Ba học sinh được chọn là bất kì.
  - b) Ba học sinh được chọn gồm 1 nam và 2 nữ.
  - c) Có ít nhất một nam trong ba học sinh được chọn.
- 8.26. Trong khai triển nhị thức Newton của  $(2x + 3)^5$ , hệ số của  $x^4$  hay hệ số của  $x^3$  lớn hơn?

# CHƯƠNG IX TÍNH XÁC SUẤT THEO ĐỊNH NGHĨA CỔ ĐIỂN

Li thuyết Xác suất là một ngành toán học nghiên cứu các hiện tượng ngẫu nhiên. Nhà toán học Pháp P. S. Laplace đã viết "Li thuyết Xác suất ra đời từ việc nghiên cứu các trò chơi may rủi, đã và đang trở thành một trong những đối tượng quan trọng nhất của tri thức nhân loại. Phần lớn những vấn đề quan trọng nhất của cuộc sống là những bài toán của Lí thuyết Xác suất".

Chương này giới thiệu định nghĩa cổ điển của xác suất, phương pháp tổ hợp và sơ đồ hình cây để tính xác suất theo định nghĩa cổ điển

![](_page_77_Picture_3.jpeg)

P. S. Laplace (1749 - 1827)

Bài 26

# BIẾN CỐ VÀ ĐỊNH NGHĨA CỔ ĐIỂN CỦA XÁC SUẤT

## THUẬT NGỮ

- Biến cố đối
- Định nghĩa cổ điển của xác suất
- Nguyên lí xác suất bé

# KIẾN THỨC, KĨ NĂNG

- Nhận biết một số khái niệm: Phép thử ngấu nhiên, không gian mấu, biến cố là tập con của không gian mấu, biến cố đối, định nghĩa cổ điển của xác suất, nguyên lí xác suất bé.
- Mô tả không gian mẫu, biến cố trong một số phép thử đơn giản.
- · Mô tả tính chất cơ bản của xác suất.

Khi tham gia một trò chơi bốc thăm trúng thưởng, mỗi người chơi chọn một bộ 6 số đôi một khác nhau từ 45 số: 1; 2; ...; 45, chẳng hạn bạn An chọn bộ số {5; 13; 20; 31; 32; 35}.

Sau đó, người quản trò bốc ngẫu nhiên 6 quả bóng (không hoàn lại) từ một thùng kín đựng 45 quả bóng như nhau ghi các số 1; 2;...; 45. Bộ 6 số ghi trên 6 quả bóng đó được gọi là *bộ* số trúng thưởng.

Nếu bộ số của người chơi trùng với bộ số trúng thưởng thì người chơi trúng giải độc đắc; nếu trùng với 5 số của bộ số trúng thưởng thì người chơi trúng giải nhất.

Tính xác suất bạn An trúng giải độc đắc, giải nhất khi chơi.

Trong bài học này, ta sẽ tìm hiểu một số khái niệm cơ bản và định nghĩa cổ điển của xác suất, từ đó giúp ta có cơ sở trả lời câu hỏi nêu trên.

![](_page_77_Picture_20.jpeg)

## 1. BIẾN CỐ

Ở lớp 9 ta đã biết những khái niệm quan trọng sau:

- Phép thử ngẫu nhiên (gọi tắt là phép thử) là một thí nghiệm hay một hành động mà kết quả của nó không thể biết được trước khi phép thử được thực hiện.
- Không gian mẫu của phép thử là tập hợp tất cả các kết quả có thể khi thực hiện phép thử. Không gian mẫu của phép thử được kí hiệu là Ω.
- Kết quả thuận lợi cho một biến cố E liên quan tới phép thử T là kết quả của phép thử T làm cho biến cố đó xảy ra.

Chú ý. Ta chỉ xét các phép thử mà không gian mẫu gồm hữu hạn kết quả.

Ví dụ 1. Một tổ trong lớp 10A có ba học sinh nữ là Hương, Hồng, Dung và bốn học sinh nam là Sơn, Tùng, Hoàng, Tiến. Giáo viên chọn ngẫu nhiên một học sinh trong tổ đó để kiểm tra vở bài tập. Phép thử ngẫu nhiên là gì? Mô tả không gian mẫu.

#### Giải

Phép thử ngẫu nhiên là chọn ngẫu nhiên một học sinh trong tổ để kiểm tra vở bài tập.

Không gian mẫu là tập hợp tất cả các học sinh trong tổ.

Ta có  $\Omega$  = {Hương; Hồng; Dung; Sơn; Tùng; Hoàng; Tiến}.

> HD1. Trở lại Ví dụ 1, xét hai biến cố sau:

A: "Học sinh được gọi là một bạn nữ";

B: "Học sinh được gọi có tên bắt đầu bằng chữ H".

Hãy liệt kê các kết quả thuận lợi cho biến cố A, B.

Theo định nghĩa, ta thấy mỗi kết quả thuận lợi cho biến cố E chính là một phần tử thuộc không gian mẫu  $\Omega$ . Do đó về mặt toán học, ta có:

Mỗi biến cố là một tập con của không gian mẫu Ω. Tập con này là tập tất cả các kết quả thuận lợi cho biến cố đó.

![](_page_78_Picture_17.jpeg)

Không gian mẫu  $\Omega$  và biến cố E

Nhận xét. Biến cố chắc chắn là tập  $\Omega$ , biến cố không thể là tập  $\emptyset$ .

- **>>> Ví dụ 2.** Trở lại *tình huống mở đầu* về trò chơi bốc thăm trúng thưởng.
  - a) Phép thử là gì? Mô tả không gian mẫu  $\Omega$ .
  - b) Gọi F là biến cố: "Bạn An trúng giải độc đắc". Hỏi F là tập con nào của không gian mẫu?
  - c) Gọi G là biến cố: "Bạn An trúng giải nhất". Hãy chỉ ra ba phần tử của tập G. Từ đó, hãy mô tả tập hợp G bằng cách chỉ ra tính chất đặc trưng cho các phần tử của tập G.

#### Giải

- a) Phép thử là chọn ngẫu nhiên 6 số trong 45 số: 1; 2;...; 45. Không gian mẫu  $\Omega$  là tập hợp tất cả các tập con có sáu phần tử của tập  $\{1; 2;...; 44; 45\}$ .
- b)  $F = \{5, 13, 20, 31, 32, 35\}.$

c) Ba phần tử thuộc G chẳng hạn là:

G là tập hợp tất cả các tập con gồm sáu phần tử của tập {1: 2: 3:...: 45} có tính chất: năm phần tử của nó thuộc tập {5; 13; 20; 31; 32; 35} và một phần tử còn lại không thuộc tập {5; 13; 20; 31; 32; 35}.

- **Luyên tập 1.** Phần thưởng trong một chương trình khuyến mãi của một siêu thị là: tị vị, bàn ghế, tủ lạnh, máy tính, bếp từ, bộ bát đĩa. Ông Dũng tham gia chương trình được chọn ngẫu nhiên một mặt hàng.
  - a) Mô tả không gian mẫu.
  - b) Gọi D là biến cố: "Ông Dũng chọn được mặt hàng là đồ điện". Hỏi D là tập con nào của không gian mẫu?
- 🎾 🚻 ----------------------------------xảy ra?

Ta thấy biến cố C xảy ra khi và chỉ khi biến cố A không xảy ra.

Ta nói biến cố C là biến cố đối của A.

![](_page_79_Picture_9.jpeg)

Biến cố đối của biến cố E là biến cố "E không xảy ra". Biến cố đối của E được kí hiệu là E.

Nhận xét. Nếu biến cố E là tập con của không gian mẫu  $\Omega$  thì biến cố đối  $\overline{E}$  là tập tất cả các phần tử của  $\Omega$  mà không là phần tử của E. Vậy biến cố  $\overline{E}$  là phần bù của E trong  $\Omega$ :  $\overline{E} = C_0 E$ .

- 冽 **Ví dụ 3.** Gieo một con xúc xắc 6 mặt và quan sát số chấm xuất hiện trên con xúc xắc.
  - a) Mô tả không gian mẫu.
  - VỚI CUỐC SỐNG b) Gọi M là biến cố: "Số chấm xuất hiện trên con xúc xắc là một số chẵn". Nội dung biến cố đối M của M là gì?
  - c) Biến cố M và  $\overline{M}$  là tập con nào của không gian mẫu?

#### Giải

- a) Không gian mẫu  $\Omega = \{1, 2, 3, 4, 5, 6\}$ .
- b) Biến cố đối  $\overline{M}$  của M là biến cố: "Số chấm xuất hiện trên con xúc xắc là một số lẻ".
- c) Ta có  $M = \{2; 4; 6\} \subset \Omega$ ;  $\overline{M} = C_0 M = \{1; 3; 5\} \subset \Omega$ .
- **Luyện tập 2.** Gieo một con xúc xắc. Gọi K là biến cố: "Số chấm xuất hiện trên con xúc xắc là một số nguyên tố".
  - a) Biến cố: "Số chấm xuất hiện trên con xúc xắc là một hợp số" có là biến cố  $\overline{K}$  không?
  - b) Biến cố K và  $\overline{K}$  là tập con nào của không gian mẫu?

# 2. ĐỊNH NGHĨA CỔ ĐIỂN CỦA XÁC SUẤT

Ở lớp 9 ta đã học những kiến thức cơ bản sau:

- Các kết quả có thể của phép thử T gọi là đồng khả năng nếu chúng có khả năng xuất hiện như nhau.
- Giả sử các kết quả có thể của phép thử T là đồng khả năng. Khi đó xác suất của biến cố E bằng tỉ số giữa số kết quả thuận lợi của E và số kết quả có thể.
- №3. Một hộp chứa 12 tấm thẻ được đánh số 1; 2; 3; 4; 5; 6; 7; 8; 9; 10; 11; 12. Rút ngấu nhiên từ hộp đó một tấm thẻ.
  - a) Mô tả không gian mẫu  $\Omega$ . Các kết quả có thể có đồng khả năng không?
  - b) Xét biến cố E: "Rút được thẻ ghi số nguyên tố". Biến cố E là tập con nào của không gian mẫu?
  - c) Phép thử có bao nhiêu kết quả có thể? Biến cố E có bao nhiêu kết quả thuận lợi? Từ đó, hãy tính xác suất của biến cố E.

Ta đã biết không gian mẫu  $\Omega$  của phép thử T là tập hợp tất cả các kết quả có thể của T; biến cố E liên quan đến phép thử T là tập con của  $\Omega$ . Vì thế số kết quả có thể của phép thử T chính là số phần tử tập  $\Omega$ ; số kết quả thuận lợi của biến cố E chính là số phần tử của tập E. Do đó, ta có định nghĩa cổ điển của xác suất như sau:

Cho phép thử T có không gian mẫu là  $\Omega$ . Giả thiết rằng các kết quả có thể của T là đồng khả năng. Khi đó nếu E là một biến cố liên quan đến phép thử T thì xác suất của E được cho bởi công thức

$$P(E) = \frac{n(E)}{n(\Omega)},$$

trong đó  $n(\Omega)$  và n(E) tương ứng là số phần tử của tập  $\Omega$  và tập E.

## Nhận xét

- Với mỗi biến cố E, ta có 0 ≤ P(E) ≤ 1.
- Với biến cố chắc chắn (là tập  $\Omega$ ), ta có  $P(\Omega) = 1$
- Với biến cố không thể (là tập  $\emptyset$  ), ta có  $P(\emptyset) = 0$ .
- Từ định nghĩa cổ điển của xác suất, hãy chứng minh các nhận xét trên.
- Ví dụ 4. Gieo một đồng xu cân đối liên tiếp ba lần. Gọi E là biến cố: "Có hai lần xuất hiện mặt sấp và một lần xuất hiện mặt ngửa". Tính xác suất của biến cố E.

## Giai

Kí hiệu S và N tương ứng là đồng xu ra mặt sấp và đồng xu ra mặt ngửa.

Không gian mẫu  $\Omega$  = {SSN; SNS; SNN; SSS; NSN; NNS; NNN; NSS}.

 $E = \{SSN; SNS; NSS\}.$ 

Ta có  $n(\Omega)$  = 8; n(E) = 3. Do đồng xu cân đối nên các kết quả có thể là đồng khả năng.

$$V\hat{a}y P(E) = \frac{n(E)}{n(\Omega)} = \frac{3}{8}.$$

Ví dụ 5. Hai túi I và II chứa các tấm thẻ được đánh số. Túi I: {1; 2; 3; 4; 5}, túi II: {1; 2; 3; 4}. Rút ngẫu nhiên một tấm thẻ từ mỗi túi I và II. Tính xác suất để tổng hai số trên hai tấm thẻ lớn hơn 6.

![](_page_81_Picture_1.jpeg)

#### Giải

Mô tả không gian mẫu  $\Omega$  bằng cách lập bảng như sau.

| Túi II<br>Túi I | 1      | 2      | 3      | 4      |
|-----------------|--------|--------|--------|--------|
| 1               | (1, 1) | (1, 2) | (1, 3) | (1, 4) |
| 2               | (2, 1) | (2, 2) | (2, 3) | (2, 4) |
| 3               | (3, 1) | (3, 2) | (3, 3) | (3, 4) |
| 4               | (4, 1) | (4, 2) | (4, 3) | (4, 4) |
| 5               | (5, 1) | (5, 2) | (5, 3) | (5, 4) |

Mỗi ô là một kết quả có thể. Có 20 ô, vậy  $n(\Omega) = 20$ .

Biến cố E: "Tổng hai số trên hai tấm thẻ lớn hơn 6" xảy ra khi tổng là một trong ba trường hợp:

Tổng bằng 7 gồm các kết quả: (3, 4); (4, 3); (5, 2).

Tổng bằng 8 gồm các kết quả: (4, 4); (5, 3).

Tổng bằng 9 có một kết quả: (5, 4).

Vậy biến cố  $E = \{(3, 4); (4, 3); (5, 2); (4, 4); (5, 3); (5, 4)\}$ . Từ đó n(E) = 6 và  $P(E) = \frac{6}{20} = \frac{3}{10} = 0, 3$ .

Chú ý. Trong những phép thử đơn giản, ta đếm số phần tử của tập  $\Omega$  và số phần tử của biến cố E bằng cách liệt kê ra tất cả các phần tử của hai tập hợp này.

Luyện tập 3. Gieo đồng thời hai con xúc xắc cân đối. Tính xác suất để tổng số chấm xuất hiện trên hai con xúc xắc bằng 4 hoặc bằng 6.

# 3. NGUYÊN LÍ XÁC SUẤT BÉ

Qua thực tế người ta thấy rằng một biến cố có xác suất rất bé thì sẽ không xảy ra khi ta thực hiện một phép thử hay một vài phép thử. Từ đó người ta đã thừa nhận nguyên lí sau đây gọi là nguyên lí xác suất bé:

Nếu một biến cố có xác suất rất bé thì trong một phép thử biến cố đó sẽ không xảy ra.

Chẳng hạn, xác suất một chiếc máy bay rơi là rất bé, khoảng 0,00000027. Mỗi hành khách khi đi máy bay đều tin rằng biến cố: "Máy bay rơi" sẽ không xảy ra trong chuyến bay của mình, do đó người ta vẫn không ngần ngại đi máy bay.

Chú ý. Trong thực tế, xác suất của một biến cố được coi là bé phụ thuộc vào từng trường hợp cụ thể. Chẳng hạn, xác suất một chiếc điện thoại bị lỗi kĩ thuật là 0,001 được coi là rất bé, nhưng nếu xác suất cháy nổ động cơ của một máy bay là 0,001 thì xác suất này không được coi là rất bé.

>> Vân dung. Xác suất của biến cố có ý nghĩa thực tế như sau:

Giả sử biến cố A có xác suất P(A). Khi thực hiện phép thử n lần ( $n \ge 30$ ) thì số lần xuất hiện biến cố A sẽ xấp xỉ bằng  $n \cdot P(A)$  (nói chung khi n càng lớn thì sai số tương đối càng bé).

Giả thiết rằng xác suất sinh con trai là 0,512 và xác suất sinh con gái là 0,488. Vận dụng ý nghĩa thực tế của xác suất, hãy ước tính trong số trẻ mới sinh với 10 000 bé gái thì có bao nhiêu bé trai.

*Hướng dẫn.* Gọi n là số trẻ mới sinh. Ta coi mỗi lần sinh là một phép thử và biến cố liên quan đến phép thử là biến cố: "Sinh con gái". Như vậy ta có n phép thử. Ước tính n, từ đó ước tính số bé trai.

# **BÀI TẬP**

- 9.1. Chọn ngẫu nhiên một số nguyên dương không lớn hơn 30.
  - a) Mô tả không gian mẫu.
  - b) Gọi A là biến cố: "Số được chọn là số nguyên tố". Các biến cố A và  $\overline{A}$  là tập con nào của không gian mẫu?
- 9.2. Chọn ngẫu nhiên một số nguyên dương không lớn hơn 22.
  - a) Mô tả không gian mẫu.
  - b) Gọi B là biến cố: "Số được chọn chia hết cho 3". Các biến cố B và  $\overline{B}$  là các tập con nào của không gian mẫu?
- 9.3. Gieo đồng thời một con xúc xắc và một đồng xu.
  - a) Mô tả không gian mẫu.
  - b) Xét các biến cố sau:
    - C: "Đồng xu xuất hiện mặt sấp";
    - D: "Đồng xu xuất hiện mặt ngửa hoặc số chấm xuất hiện trên con xúc xắc là 5".

Các biến cố C,  $\overline{C}$ , D và  $\overline{D}$  là các tập con nào của không gian mẫu?

- 9.4. Một túi có chứa một số bi xanh, bi đỏ, bi đen và bi trắng. Lấy ngẫu nhiên một viên bi từ trong túi.
  - a) Gọi H là biến cố: "Bi lấy ra có màu đỏ". Biến cố: "Bi lấy ra có màu xanh hoặc màu đen hoặc trắng" có phải là biến cố  $\overline{H}$  hay không?
  - b) Gọi K là biến cố: "Bi lấy ra có màu xanh hoặc màu trắng". Biến cố: "Bi lấy ra màu đen" có phải là biến cố  $\overline{K}$  hay không?
- 9.5. Hai bạn An và Bình mỗi người gieo một con xúc xắc cân đối. Tính xác suất để:
  - a) Số chấm xuất hiện trên hai con xúc xắc bé hơn 3;
  - b) Số chấm xuất hiện trên con xúc xắc mà An gieo lớn hơn hoặc bằng 5;
  - c) Tích hai số chấm xuất hiện trên hai con xúc xắc bé hơn 6;
  - d) Tổng hai số chấm xuất hiện trên hai con xúc xắc là một số nguyên tố.

# THỰC HÀNH TÍNH XÁC SUẤT THEO ĐỊNH NGHĨA CỔ ĐIỂN

# THUẬT NGỮ

Xác suất của biến cố đối.

# KIẾN THỨC, KĨ NĂNG

- Tính xác suất trong một số bài toán đơn giản bằng phương pháp tổ hợp.
- Tính xác suất trong một số bài toán đơn giản bằng cách sử dụng sơ đồ hình cây.
- Nắm và vận dụng quy tắc tính xác suất của biến cố đối.

Trở lại *tình huống mở đầu* trong Bài 26. Hãy tính xác suất trúng giải độc đắc, trúng giải nhất của bạn An khi chọn bộ số {5; 13; 20; 31; 32; 35}.

# 1. SỬ DỤNG PHƯƠNG PHÁP TỔ HỢP

**H91.** Theo định nghĩa cổ điển của xác suất, để tính xác suất của biến cố F: "Bạn An trúng giải độc đắc" và biến cố G: "Bạn An trúng giải nhất" ta cần xác định  $n(\Omega)$ , n(F) và n(G). Liệu có thể tính  $n(\Omega)$ , n(F) và n(G) bằng cách liệt kê ra hết các phần tử của  $\Omega$ , F và G rồi kiểm đếm được không?

Trong nhiều bài toán, để tính số phần tử của không gian mẫu, của các biến cố, ta thường sử dụng các quy tắc đếm, các công thức tính số hoán vị, chỉnh hợp và tổ hợp.

Đôi khi người ta gọi Đại số tổ hợp là "sự kiểm đếm không cần phải liệt kê".

![](_page_83_Picture_13.jpeg)

![](_page_83_Picture_14.jpeg)

## Giải

Không gian mẫu là tập tất cả các tập con gồm 6 học sinh trong 10 học sinh. Vậy

$$n(\Omega) = C_{10}^6 = 210$$
.

a) Tập C chỉ có một phần tử là tập 6 học sinh nam. Vậy 
$$n(C) = 1$$
, do đó  $P(C) = \frac{1}{210}$ .

b) Mỗi phần tử của D được hình thành từ hai công đoạn. Công đoạn 1. Chọn 4 học sinh nam từ 6 học sinh nam, có  $C_6^4 = 15$  (cách chọn).

Công đoạn 2. Chọn 2 học sinh nữ từ 4 học sinh nữ, có  $C_4^2 = 6$  (cách chọn).

Theo quy tắc nhân, tập D có  $15 \cdot 6 = 90$  (phần tử). Vậy n(D) = 90. Từ đó  $P(D) = \frac{90}{210} = \frac{3}{7}$ .

![](_page_83_Picture_23.jpeg)

**Luyện tập 1.** Một tổ trong lớp 10B có 12 học sinh, trong đó có 7 học sinh nam và 5 học sinh nữ. Giáo viên chọn ngẫu nhiên 6 học sinh trong tổ để kiểm tra vở bài tập Toán. Tính xác suất để trong 6 học sinh được chọn số học sinh nữ bằng số học sinh nam.

# 2. SỬ DUNG SƠ ĐỔ HÌNH CÂY

H92. Trong trò chơi "Vòng quay may mắn", người chơi sẽ quay hai bánh xe. Mũi tên ở bánh xe thứ nhất có thể dừng ở một trong hai vị trí: Loại xe 50 cc và Loại xe 110 cc. Mũi tên ở bánh xe thứ hai có thể dừng ở một trong bốn vị trí: màu đen, màu trắng, màu đỏ và màu xanh. Vị trí của mũi tên trên hai bánh xe sẽ xác định người chơi nhận được loại xe nào, màu gì.

![](_page_84_Picture_3.jpeg)

Phép thử T là quay hai bánh xe. Hãy vẽ sơ đồ hình cây mô tả các phần tử của không gian mẫu.

Trong một số bài toán, phép thử *T* được hình thành từ một vài phép thử, chẳng hạn: gieo xúc xắc liên tiếp bốn lần; lấy ba viên bi, mỗi viên từ một hộp;... Khi đó ta sử dụng sơ đồ hình cây để có thể mô tả đầy đủ, trực quan không gian mẫu và biến cố cần tính xác suất.

- >> Ví dụ 2. Có ba chiếc hộp. Hộp I có chứa ba viên bi: 1 viên màu đỏ, 1 viên màu xanh và 1 viên màu vàng. Hộp II chứa hai viên bi: 1 viên màu xanh và 1 viên màu vàng. Hộp III chứa hai viên bi: 1 viên màu đỏ và 1 viên màu xanh. Từ mỗi hộp ta lấy ngẫu nhiên một viên bi.
  - a) Vẽ sơ đồ hình cây để mô tả các phần tử của không gian mẫu.
  - b) Tính xác suất để trong ba viên bi lấy ra có đúng một viên bi màu xanh.

## Giải

a) Kí hiệu Đ, X, V tương ứng là viên bị màu đỏ, màu xanh và màu vàng.

![](_page_84_Picture_11.jpeg)

Đường đi màu đỏ ứng với kết quả có thể ĐXĐ.

![](_page_84_Picture_13.jpeg)

Các kết quả có thể là: ĐXĐ, ĐXX, ĐVĐ, ĐVX, XXĐ, XXX, XVĐ, XVX, VXĐ, VXX, VVĐ, VVX. Do đó  $\Omega$  = {ĐXĐ; ĐXX; ĐVĐ; ĐVX; XXĐ; XXX; XVĐ; XVX; VXĐ; VXX; VVĐ; VVX}. Vậy  $n(\Omega) = 12$ .

b) Gọi K là biến cố: "Trong ba viên bi lấy ra có đúng một viên bi màu xanh". Ta có

$$K = \{DXD; DVX; XVD; VXD; VVX\}. Vậy  $n(K) = 5. Từ đó$$$

$$P(K) = \frac{n(K)}{n(\Omega)} = \frac{5}{12}.$$

- Luyện tập 2. Trở lại trò chơi "Vòng quay may mắn" ở HĐ2. Tính xác suất để người chơi nhận được loại xe 110 cc có màu trắng hoặc màu xanh.
- Luyện tập 3. Trong một cuộc tổng điều tra dân số, điều tra viên chọn ngẫu nhiên một gia đình có ba người con và quan tâm giới tính của ba người con này.
  - a) Vẽ sơ đồ hình cây để mô tả các phần tử của không gian mẫu.
  - b) Giả thiết rằng khả năng sinh con trai và khả năng sinh con gái là như nhau. Tính xác suất để gia đình đó có một con trai và hai con gái.

# 3. XÁC SUẤT CỦA BIẾN CỐ ĐỐI

 $\rho$  H93. Cho E là một biến cố và  $\Omega$  là không gian mẫu. Tính  $n(\overline{E})$  theo  $n(\Omega)$  và n(E).

Ta có công thức sau đây liên hệ giữa xác suất của một biến cố với xác suất của biến cố đối.

Cho E là một biến cố. Xác suất của biến cố  $\overline{E}$  liên hệ với xác suất của E bởi công thức sau:

$$P(\overline{E}) = 1 - P(E)$$
.

- Ví dụ 3. Chọn ngẫu nhiên hai số từ tập {1; 2; ...; 9}. Gọi H là biến cố: "Trong hai số được chọn có ít nhất một số chẵn".
  - a) Mô tả không gian mẫu.
  - b) Biến cố  $\overline{H}$  là tập con nào của không gian mẫu?
  - c) Tính  $P(\overline{H})$  và P(H).

#### Giai

- a) Không gian mẫu là tập tất cả các tập con có 2 phần tử của tập {1; 2; ...; 8; 9}.
- b) Biến cố  $\overline{H}$ : "Cả hai số được chọn đều là số lẻ". Khi đó  $\overline{H}$  là tập tất cả các tập con có 2 phần tử của tập số lẻ {1; 3; 5; 7; 9}.
- c) Ta có  $n(\Omega) = C_9^2 = 36$ ,  $n(\overline{H}) = C_5^2 = 10$ . Vậy  $P(\overline{H}) = \frac{10}{36} = \frac{5}{18}$ .

Từ đó 
$$P(H) = 1 - P(\overline{H}) = 1 - \frac{5}{18} = \frac{13}{18}$$
.

Chú ý. Trong một số bài toán, nếu tính trực tiếp xác suất của biến cố gặp khó khăn, ta có thể tính gián tiếp bằng cách tính xác suất của biến cố đối của nó.

- **Luyện tập 4.** Có ba hộp A, B, C. Hộp A có chứa ba thẻ mang số 1, số 2 và số 3. Hộp B chứa hai thẻ mang số 2 và số 3. Hộp C chứa hai thẻ mang số 1 và số 2. Từ mỗi hộp ta rút ra ngẫu nhiên một thẻ.
  - a) Vẽ sơ đồ hình cây để mô tả các phần tử của không gian mẫu.
  - b) Gọi M là biến cố: "Trong ba thẻ rút ra có ít nhất một thẻ số 1". Biến cố  $\overline{M}$  là tập con nào của không gian mẫu?
  - c) Tính P(M) và  $P(\overline{M})$ .
- >> Vận dụng. Giải bài toán trong tình huống mở đầu.

Hướng dẫn. Vì Ω là tập tất cả các tập con có 6 phần tử của tập {1; 2;...; 44; 45} nên

$$n(\Omega) = C_{45}^6$$
.

Gọi F là biến cố: "Bạn An trúng giải độc đắc". F là tập hợp có duy nhất một phần tử là tập  $\{5; 13; 20; 31; 32; 35\}$ . Vậy n(F) = 1. Từ đó tính được P(F).

Gọi G là biến cố: "Bạn An trúng giải nhất". G là tập hợp tấp cả các tập con gồm sáu phần tử của tập {1; 2; 3;...; 45} có tính chất:

- 1. Năm phần tử của G thuộc tập {5; 13; 20; 31; 32; 35}.
- 2. Một phần tử còn lại của G không thuộc tập {5; 13; 20; 31; 32; 35}.

Mỗi phần tử của G được hình thành từ hai công đoạn.

Công đoạn 1. Chọn năm phần tử trong tập  $\{5; 13; 20; 31; 32; 35\}$ , có  $C_6^5 = 6$  (cách chọn).

*Công đoạn 2.* Chọn một phần tử còn lại trong 39 phần tử không thuộc tập  $\{5; 13; 20; 31; 32; 35\}$ , có  $C_{39}^1 = 39$  (cách chọn).

Theo quy tắc nhân, tập G có  $6 \cdot 39 = 234$  (phần tử). Vậy n(G) = 234. Từ đó tính được P(G).

# **BÀI TẬP**

- 9.6. Chọn ngẫu nhiên một gia đình có ba con và quan sát giới tính của ba người con này. Tính xác suất của các biến cố sau:
  - a) A: "Con đầu là gái";
  - b) B: "Có ít nhất một người con trai".
- 9.7. Một hộp đựng các tấm thẻ đánh số 10; 11;...; 20. Rút ngẫu nhiên từ hộp hai tấm thẻ. Tính xác suất của các biến cố sau:
  - a) C: "Cả hai thẻ rút được đều mang số lẻ";
  - b) D: "Cả hai thẻ rút được đều mang số chẵn".
- 9.8. Một chiếc hộp đựng 6 viên bi trắng, 4 viên bi đỏ và 2 viên bi đen. Chọn ngẫu nhiên ra 6 viên bi. Tính xác suất để trong 6 viên bi đó có 3 viên bi trắng, 2 viên bi đỏ và 1 viên bi đen.
- 9.9. Gieo liên tiếp một con xúc xắc và một đồng xu.
  - a) Vễ sơ đồ hình cây mô tả các phần tử của không gian mẫu.
  - b) Tính xác suất của các biến cố sau:
  - F: "Đồng xu xuất hiện mặt ngửa";
  - G: "Đồng xu xuất hiện mặt sấp hoặc số chấm xuất hiện trên con xúc xắc là 5".

- 9.10. Trên một phố có hai quán ăn X, Y. Ba bạn Sơn, Hải, Văn mỗi người chọn ngẫu nhiên một quán ăn.
  - a) Vẽ sơ đồ hình cây mô tả các phần tử của không gian mẫu.
  - b) Tính xác suất của biến cố "Hai bạn vào quán X, bạn còn lại vào quán Y".
- 9.11. Gieo lần lượt hai con xúc xắc cân đối. Tính xác suất để ít nhất một con xúc xắc xuất hiện mặt 6 chấm.
- 9.12. Màu hạt của đậu Hà Lan có hai kiểu hình là màu vàng và màu xanh tương ứng với hai loại gen là gen trội A và gen lặn a. Hình dạng hạt của đậu Hà Lan có hai kiểu hình là hạt trơn và hạt nhăn tương ứng với hai loại gen là gen trội B và gen lặn b. Biết rằng, cây con lấy ngẫu nhiên một gen từ cây bố và một gen từ cây mẹ.

Phép thử là cho lai hai loại đậu Hà Lan, trong đó cả cây bố và cây mẹ đều có kiểu gen là (*Aa*, *Bb*) và kiểu hình là hạt màu vàng và trơn. Giả sử các kết quả có thể là đồng khả năng. Tính xác suất để cây con cũng có kiểu hình là hạt màu vàng và trơn.

### Em có biết?

Năm 1652, nhà toán học Pascal nhận được một bức thư từ một nhà quý tộc nhờ ông giải đáp câu hỏi sau:

"Khi tham gia một trò chơi, người chơi được chọn một trong ba phương án sau:

- Phương án 1: Được gieo con xúc xắc cân đối liên tiếp 6 lần. Người chơi thắng nếu có ít nhất một lần xuất hiện mặt 6 chấm.
- Phương án 2: Được gieo con xúc xắc cân đối liên tiếp 12 lần. Người chơi thắng nếu có ít nhất hai lần xuất hiện mặt 6 chấm.
- Phương án 3: Được gieo con xúc xắc cân đối liên tiếp 18 lần. Người chơi thắng nếu có ít nhất ba lần xuất hiện mặt 6 chấm.

Người chơi nên chọn phương án nào?"

Pascal đã tính ra xác suất thắng của Phương án 1 là 0,665; của Phương án 2 là 0,619 và của Phương án 3 là 0,597. Do đó, ông khuyên nhà quý tộc nên chọn Phương án 1.

# BÀI TẬP CUỐI CHƯƠNG IX

## A - TRẮC NGHIỆM

- 9.13. Một hộp có bốn loại bi: bi xanh, bi đỏ, bi trắng và bi vàng. Lấy ngẫu nhiên ra một viên bi. Goi E là biến cố: "Lấy được viên bi đỏ". Biến cố đối của E là biến cố
  - A Lấy được viên bi xanh.
  - B. Lấy được viên bi vàng hoặc bi trắng.
  - Lấy được viên bi trắng.
  - D. Lấy được viên bi vàng hoặc bi trắng hoặc bi xanh.
- 9.14. Rút ngẫu nhiên ra một thẻ từ một hộp có 30 tấm thẻ được đánh số từ 1 đến 30. Xác suất để số trên tấm thẻ được rút ra chia hết cho 5 là
  - A.  $\frac{1}{30}$ .
- B.  $\frac{1}{5}$
- C.  $\frac{1}{3}$ .
- D.  $\frac{2}{5}$ .
- 9.15. Gieo hai con xúc xắc cân đối. Xác suất để tổng số chấm xuất hiện trên hai con xúc xắc không lớn hơn 4 là
  - A.  $\frac{1}{7}$

- **B.**  $\frac{1}{6}$
- C.  $\frac{1}{8}$
- D.  $\frac{2}{9}$
- 9.16. Một tổ trong lớp 10T có 4 bạn nữ và 3 bạn nam. Giáo viên chọn ngẫu nhiên hai bạn trong tổ đó tham gia đội làm báo của lớp. Xác suất để hai bạn được chọn có một bạn nam và một bạn nữ là
  - A.  $\frac{4}{7}$

- B.  $\frac{2}{7}$
- c.  $\frac{1}{6}$
- D.  $\frac{2}{21}$ .

# B - TƯ LUÂN

9.17. Một hộp đựng bảy thẻ màu xanh đánh số từ 1 đến 7; năm thẻ màu đỏ đánh số từ 1 đến 5 và hai thẻ màu vàng đánh số từ 1 đến 2. Rút ngẫu nhiên ra một tấm thẻ.

VỚI CUỐC SỐNG

- a) Mô tả không gian mẫu.
- b) Mỗi biến cố sau là tập con nào của không gian mẫu?
- A: "Rút ra được thẻ màu đỏ hoặc màu vàng";
- B: "Rút ra được thẻ mang số hoặc là 2 hoặc là 3".
- 9.18. Có hộp I và hộp II, mỗi hộp chứa 5 tấm thẻ đánh số từ 1 đến 5. Từ mỗi hộp, rút ngẫu nhiên ra một tấm thẻ. Tính xác suất để thẻ rút ra từ hộp II mang số lớn hơn số trên thẻ rút ra từ hộp I.
- 9.19. Gieo đồng thời hai con xúc xắc cân đối. Tính xác suất để:
  - a) Tổng số chấm trên hai con xúc xắc bằng 8;
  - b) Tổng số chấm trên hai con xúc xắc nhỏ hơn 8.

- 9.20. Dự báo thời tiết trong ba ngày thứ Hai, thứ Ba, thứ Tư của tuần sau cho biết, trong mỗi ngày này, khả năng có mưa và không mưa như nhau.
  - a) Về sơ đồ hình cây mô tả không gian mẫu.
  - b) Tính xác suất của các biến cố:
  - F: "Trong ba ngày, có đúng một ngày có mưa";
  - G: "Trong ba ngày, có ít nhất hai ngày không mưa".
- 9.21. Gieo một đồng xu cân đối liên tiếp bốn lần.
  - a) Vễ sơ đồ hình cây mô tả không gian mẫu.
  - b) Tính xác suất để trong bốn lần gieo đó có hai lần xuất hiện mặt sấp và hai lần xuất hiện mặt ngửa.
- 9.22. Chọn ngẫu nhiên 4 viên bi từ một túi đựng 4 viên bi đỏ và 6 viên bi xanh đôi một khác nhau. Gọi A là biến cố: "Trong bốn viên bi đó có cả bi đỏ và cả bi xanh". Tính P(A) và  $P(\overline{A})$ .

## Em có biết?

Về một số thành tựu của nhà toán học Pascal

Năm 16 tuổi, Pascal công bố một công trình toán học có nhan đề "Về thiết diện của đường conic", trong đó ông đã chứng minh một định lí, sau này được gọi là "Định lí Pascal về lục giác thần kì". Từ định lí này, người ta đã rút ra 400 hệ quả thú vị về hình học. Năm 17 tuổi Pascal đã chế tạo ra chiếc máy tính đầu tiên trong lịch sử nhân loại làm được bốn phép tính cộng, trừ, nhân, chia.

Năm 28 tuổi, Pascal đã toán học hoá các trò chơi may rủi để khai sinh ra lí thuyết Xác suất. Không chỉ là một nhà toán học lớn, Pascal còn là một nhà triết học, nhà vật lí và nhà văn lớn. Một số câu nói nổi tiếng của Pascal:

![](_page_89_Picture_13.jpeg)

Blaise Pascal (1623 - 1662)

"Con người chỉ là một cây sậy, một vật rất yếu đuối của tự nhiên nhưng là một cây sậy biết suy nghĩ"; "Trái tim có những lí lẽ mà lí trí không giải thích được".

(Theo review.siu.edu.vn/nhan-vat-su-kien/ và www.tudiendanhngon.vn/).

![](_page_90_Figure_0.jpeg)

# MỘT SỐ NỘI DUNG CHO HOẠT ĐỘNG TRẢI NGHIỆM HÌNH HỌC

Em có thể thực hành trải nghiệm hình học với nhiều mức độ khác nhau, từ trải nghiệm nhanh, gọn tới các trải nghiệm cần nhiều thời gian và sự chuẩn bị, từ trải nghiệm cá nhân tới trải nghiệm theo nhóm. Sau đây là một số gợi ý.

![](_page_90_Picture_3.jpeg)

Ngày 27/01/1921, Einstein đã có bài thuyết trình về chủ đề Hình học và trải nghiệm tại Viện Hàn lâm Khoa học Hoàng gia Phổ

# 1. KIỂM TRA TÍNH ĐÚNG ĐẮN CỦA MỘT KẾT QUẢ HÌNH HỌC THÔNG QUA NHỮNG VÍ DU CU THỂ

Trong chương trình, em đã được học nhiều kết quả hình học, chẳng hạn, các định lí sin, côsin, công thức tính diện tích tam giác. Tuy vậy, sách giáo khoa chủ yếu thừa nhận chúng mà không nêu phép chứng minh đầy đủ. Mặc dù trước khi chấp nhận các kết quả đó, em cũng đã có những hoạt động để hình thành kiến thức, nhưng sẽ giúp ích hơn nữa cho quá trình nhận thức, nếu em làm những "thực nghiệm" nhỏ để kiểm tra tính đúng đắn của chúng qua một số trường hợp cụ thể trong thực tế, hay trên hình vẽ.

Chẳng hạn, sử dụng các thước đo độ dài, góc và máy tính bỏ túi, em có thể kiểm tra:

- a) Định lí sin đối với một tam giác nội tiếp trong một đường tròn;
- b) Định lí côsin đối với một tam giác;
- c) Đẳng thức  $ah_a = 2\sqrt{p(p-a)(p-b)(p-c)}$  đối với tam giác ABC.

Về nguyên tắc, bao giờ cũng có sai khác nhỏ giữa kết quả thực nghiệm và kết quả lí thuyết mà em đã học. Tuy vậy, nếu gặp sai khác lớn, em nên kiểm tra hoặc thực hiện lại các bước của quá trình thực nghiệm. Một điểm nữa cần lưu ý là nếu em sử dụng một thiết bị tính toán có lập trình thì rất có thể phần mềm tính toán đó có sử dụng chính công thức mà em đang muốn thực nghiệm. Tuy vậy, với mục đích học tập, thực nghiệm của em vẫn là hữu ích ngay cả trong trường hợp đó.

# 2. SỬ DỤNG KẾT QUẢ HÌNH HỌC ĐỂ TÍNH TOÁN TRONG ĐO ĐẠC THỰC TẾ

Trong hoạt động trải nghiệm này, em (nên thực hiện theo nhóm) tiến hành đo khoảng cách từ vị trí của em tới một vị trí nào đó khó đến được, nhưng có thể quan sát, và đo khoảng cách giữa hai vị trí mà em có thể quan sát được. Dụng cụ cần chuẩn bị gồm: Ba cọc tiêu, thước dây đo độ dài, thước đo góc, hai sợi dây, máy tính cầm tay. Em thực hiện các bước như đã được trình bày và thảo luận trong Bài 6.

![](_page_91_Picture_9.jpeg)

# 3. GẤP GIẨY, ĐO ĐẠC VÀ XÁC ĐỊNH CÁC YẾU TỐ CỦA BA ĐƯỜNG CONIC

Trong hoạt động này, với một đường conic đã được vẽ trên giấy (không kèm theo các yếu tố tiêu điểm, tiêu cự, tham số tiêu, đường chuẩn), em hãy tìm cách xác định vị trí các tiêu điểm, tiêu cự (đối với elip, hypebol), tiêu điểm, tham số tiêu, đường chuẩn (đối với parabol). Để thực hiện hoạt động này, em cần nhớ lại các kiến thức đã được học về các đường conic (cách chọn hệ trục toạ độ để đường conic có phương trình chính tắc, mối liên hệ giữa các hệ số trong phương trình chính tắc với các yếu tố tiêu điểm, tiêu cự, tham số tiêu, đường chuẩn). Ngoài ra, em cần lưu ý, mỗi elip, hypebol có hai trục đối xứng, đó là đường thẳng đi

qua hai tiêu điểm và đường thẳng trung trực của đoạn thẳng nối hai tiêu điểm; mỗi parabol có một trục đối xứng, đó là đường thẳng đi qua tiêu điểm và vuông góc với đường chuẩn. Bằng cách gấp giấy, em có thể xác định được các trục đối xứng của một đường conic đã được vẽ trên giấy (em có thể dùng kim châm thủng giấy, hoặc dùng bút tô đậm đường conic, để có thể quan sát nó từ cả mặt sau của giấy).

Hướng dẫn:

Bước 1: Gấp giấy để xác định trục đối xứng của đường conic.

Bước 2: Chọn hệ trục toạ độ để với hệ trục đó, đường conic đang xét có phương trình chính tắc (chọn đơn vị đo, chẳng hạn, cm).

Bước 3: Gọi phương trình chính tắc của đường conic (theo đơn vị đo đã chọn).

Bước 4: Lấy các điểm thuộc đường conic và đo khoảng cách từ điểm đó tới các trục toạ độ (đối với elip, hypebol cần lấy 2 điểm, đối với parabol chỉ cần lấy 1 điểm). Từ đó xác định toạ độ của các điểm vừa lấy.

Bur'oc 5: Thay toạ độ của các điểm vừa lấy vào phương trình của đường conic để tính a, b (đối với elip, hyperbol) và p (đối với parabol).

Bước 6: Xác định phương trình chính tắc của đường conic, từ đó xác định vị trí các tiêu điểm, tiêu cự (đối với elip, hypebol), tiêu điểm, đường chuẩn (đối với parabol).

# 4. THỰC HÀNH TRẢI NGHIỆM TRONG PHÒNG MÁY

Em thực hiện hoạt động này với phần mềm vẽ hình GeoGebra.

- Vẽ đường tròn (A; R) và điểm B nằm ngoài đường tròn đó. Lấy một điểm C trên đường tròn (A; R) và vẽ M là giao điểm của AC và đường trung trực của đoạn thẳng BC. Cho điểm C thay đổi và dùng lệnh tìm quỹ tích để thấy rằng M thay đổi trên một nhánh hypebol.
- Vẽ đường tròn (A; R) và điểm B nằm trong đường tròn đó. Lấy một điểm C trên đường tròn (A; R) và vẽ M là giao điểm của AC và đường trung trực của đoạn thẳng BC. Cho điểm C thay đổi và dùng lệnh tìm quỹ tích để thấy rằng M thay đổi trên một elip.
- Vẽ một số đường tròn (ω₁), (ω₂), (ω₃),... có cùng tâm O₁ tương ứng có bán kính R₁, R₁+ a, R₁+ 2a,... và một số đường tròn (Ω₁), (Ω₂), (Ω₃),... có cùng tâm O₂, tương ứng có bán kính R₂, R₂+ a, R₂+ 2a,... (R₁≠R₂). Khi đó, em sẽ quan sát thấy các cặp giao điểm A₁, B₁; A₂,B₂; A₃,B₃;... tương ứng của (ω₁) và (Ω₁); (ω₂) và (Ω₂); (ω₃) và (Ω₃);... là cùng thuộc một nhánh của một hypebol. Kết quả này tương ứng với một hiện tượng vật lí mà em có thể quan sát được: Ném hai hòn sỏi (bằng nhau) xuống mặt hồ lặng sóng, thì em sẽ thấy hai họ đường tròn sóng nước và nói chung giao của chúng tạo nên một đường hypebol.

Chú ý. Em hoàn toàn có thể chứng minh được các kết quả quan sát nói trên.

# ƯỚC TÍNH SỐ CÁ THỂ TRONG MỘT QUẦN THỂ

Trong nghiên cứu về những quần thể động vật, một vấn đề quan trọng là ước tính số cá thể trong quần thể. Một phương pháp được sử dụng là đánh dấu và bắt lại.

Phương pháp này gồm hai bước như sau:

Bước 1. Chọn *M* cá thể từ quần thể, đánh dấu và thả chúng trở lại quần thể.

Bước 2. Sau một thời gian, chọn ngẫu nhiên n cá thể trong quần thể. Gọi k là số cá thể được đánh dấu trong n cá thể đó.

Ở bước 2, xét phép thử: chọn ngẫu nhiên một cá thể từ quần thể và xét biến cố A: "Cá thể có được đánh dấu". Gọi N là số cá thể trong quần thể. Xác suất của A là  $P(A) = \frac{M}{N}$ .

![](_page_93_Picture_6.jpeg)

![](_page_93_Picture_7.jpeg)

Trong n cá thể được chọn số cá thể được đánh dấu là k xấp xỉ với  $n \cdot P(A) = n \cdot \frac{M}{N}$  (xem mục Vận dụng Bài 26). Do vậy N được ước tính bởi công thức

$$N \approx M \cdot \frac{n}{k}$$

Ví dụ. Để ước tính số cá chưa biết trong một hồ nuôi cá, người ta đánh bắt 1 200 con, đánh dấu chúng rồi thả lại xuống hồ. Đánh bắt lần thứ hai được 1 300 con, thấy trong đó có 110 con có đánh dấu. Từ đó, ước tính số cá trong hồ là 1 200 110 ≈ 14182(con).

Chúng ta áp dụng phương pháp trên thông qua hoạt động sau đây.

# HOẠT ĐỘNG 1. Ước tính số hạt lạc trong một hộp Chuẩn bị:

Cốc:

Giấy, bút;

Một túi lạc.

![](_page_93_Picture_16.jpeg)

#### Tiến hành

Bước 1. Lấy ra 1 cốc lạc từ trong túi, đếm số lượng và đánh dấu từng hạt lạc.

Bước 2. Đổ lạc đã được đánh dấu vào lại trong túi và xáo trộn đều.

Bước 3. Lấy ra nửa cốc lạc, đếm tổng số hạt lạc và số hạt lạc có đánh dấu trong cốc.

Gọi N là tổng số hạt lạc trong túi ban đầu. Hãy dùng kết quả đếm được ở bước 3 để ước tính N.

## HOAT ĐÔNG 2. Đánh giá sai số của ước tính

Trong tiết thực hành trải nghiệm của lớp 10A, tổ của Hà đã thực hiện các bước trên, trong đó lặp lại bước 3 thêm hai lần: lần hai lấy 1 cốc lạc, lần ba lấy 1,5 cốc lạc và thu được kết quả như sau:

| Lần thứ | Số hạt (n) | Số hạt có<br>đánh dấu<br>( <i>k</i> ) |
|---------|------------|---------------------------------------|
| 1       | 51         | 4                                     |
| 2       | 103        | 11                                    |
| 3       | 155        | 16                                    |

![](_page_94_Picture_3.jpeg)

Bảng 1. Kết quả thí nghiệm

Giả sử số hạt lạc trong túi đựng là 1 000 (N=1 000) và số hạt được đánh dấu là 100 (M=100). Kí hiệu  $\widehat{N}$  là số quy tròn đến hàng đơn vị của đại lượng  $M \cdot \frac{n}{k}$ .

Dựa vào dữ liệu trong Bảng 1, em hãy hoàn thành bảng tính theo mẫu sau:

| Lần | N     | М   | n     | k   | Ñ     | Sai số<br>tuyệt đối | Sai số<br>tương đối |
|-----|-------|-----|-------|-----|-------|---------------------|---------------------|
| 1   | 1 000 | 100 | 51    | 4   | ?     | ?                   | ?                   |
| 2   | 1 000 | 100 | ?     | ?   | ?     | ?                   | ?                   |
| 3   | 1 000 | 100 | T ?ñi | 7 7 | ш (?р | ?                   | ?                   |

Bảng 2. Tính sai số

Em có nhận xét gì về sai số của việc tính xấp xỉ số hạt lạc trong túi khi n càng lớn?

#### Em có biết?

Phương pháp đánh dấu và bắt lại còn có tên là phương pháp Petersen, đặt theo tên người có ý tưởng đánh dấu cá thể trong một nghiên cứu năm 1894. Mặc dù mục đích trong nghiên cứu này là ước tính tỉ lệ cá thể bị chết, công thức ước tính N vẫn được gọi là ước lượng Petersen. Những ứng dụng đầu tiên của công thức này được thực hiện trên một số quần thể động vật như cá hồi, vịt.

Từ giữa thế kỉ XX, các nhà nghiên cứu không chỉ sử dụng phương pháp đánh dấu và bắt lại trong nghiên cứu những quần thể động vật mà còn phát triển nó để sử dụng vào việc giải quyết những vấn đề về sức khoẻ con người và một số lĩnh vực khác.

# BÀI TẬP ÔN TẬP CUỐI NĂM

# A - TRẮC NGHIỆM

1. Cho hệ bất phương trình bậc nhất hai ẩn  $\begin{cases} x+y>2 \\ x-y \le 1 \end{cases}$ . Điểm nào sau đây thuộc miền nghiệm của hệ bất phương trình đã cho?

A. (1; 1).

B. (2: 0).

C. (3: 2).

D. (3; -2).

2. Cho tam giác ABC. Có bao nhiêu điểm M thoả mãn  $|\overrightarrow{MA} + \overrightarrow{MB} + \overrightarrow{MC}| = 3$ ?

A. Vô số.

B. 1.

C. 2.

D. 3.

3. Biết rằng parabol  $v = x^2 + bx + c$  có đỉnh là I(1: 4). Khi đó giá trị của b + c là

A. 1.

D. 4.

4. Trong mặt phẳng toạ độ Oxy, cho đường thẳng  $\Delta: x + 2y - 5 = 0$ . Tìm mệnh đề sai trong các mệnh đề sau:

A. Vector  $\vec{n} = (1, 2)$  là một vector pháp tuyến của  $\Delta$ .

**B.** Vector  $\vec{u} = (2; -1)$  là một vector chỉ phương của  $\Delta$ .

C. Đường thẳng  $\Delta$  song song với đường thẳng d:  $\begin{cases} x = 1 - 2t \\ y = 1 + t \end{cases}$ 

D. Đường thẳng  $\Delta$  có hệ số góc k = 2.

5. Trong khai triển nhị thức Newton của  $(2+3x)^4$ , hệ số của  $x^2$  là

**B.**  $C_4^2$ . **C.**  $9C_4^2$ .

D. 36C<sup>2</sup>

6. Một tổ gồm 7 nam và 3 nữ. Chọn ngẫu nhiên hai người. Xác suất để trong hai người được chon có ít nhất một nữ là

A.  $\frac{7}{15}$ .

B.  $\frac{8}{15}$ .

C.  $\frac{1}{15}$ .

D.  $\frac{2}{15}$ .

# B - TƯ LUẬN

Cho các mênh đề:

P: "Tam giác ABC là tam giác vuông tai A";

Q: "Tam giác ABC có các cạnh thoả mãn  $AB^2 + AC^2 = BC^2$ ".

a) Hãy phát biểu các mệnh đề:  $P \Rightarrow Q$ ,  $Q \Rightarrow P$ ,  $P \Leftrightarrow Q$ ,  $\overline{P} \Rightarrow \overline{Q}$ . Xét tính đúng sai của các mệnh đề này.

b) Dùng các khái niệm "điều kiện cần" và "điều kiện đủ" để diễn tả mệnh đề  $P \Rightarrow Q$ .

c) Gọi X là tập hợp các tam giác ABC vuông tại A, Y là tập hợp các tam giác ABC có trung tuyến  $AM = \frac{1}{2}BC$ . Nêu mối quan hệ giữa hai tập hợp X và Y.

8. a) Biểu diễn miền nghiệm D của hệ bất phương trình bậc nhất hai ẩn sau:

$$\begin{cases} x+y \le 6 \\ 2x-y \le 2 \\ x \ge 0 \\ y \ge 0. \end{cases}$$

- b) Từ kết quả câu a, tìm giá trị lớn nhất và giá trị nhỏ nhất của biểu thức F(x,y) = 2x + 3y trên miền D.
- 9. Cho hàm số  $y = f(x) = ax^2 + bx + c$  với đồ thị là parabol (P) có đỉnh  $I\left(\frac{5}{2}; -\frac{1}{4}\right)$  và đi qua điểm A(1; 2).
  - a) Biết rằng phương trình của parabol có thể viết dưới dạng  $y = a(x h)^2 + k$ , trong đó I(h; k) là toạ độ đỉnh của parabol. Hãy xác định phương trình của parabol (P) đã cho và vẽ parabol này.
  - b) Từ parabol (P) đã vẽ ở câu a, hãy cho biết khoảng đồng biến và khoảng nghịch biến của hàm số y = f(x).
  - c) Giải bất phương trình  $f(x) \ge 0$ .
- 10. Giải các phương trình chứa căn thức sau:

a) 
$$\sqrt{2x^2-6x+3} = \sqrt{x^2-3x+1}$$
;

b) 
$$\sqrt{x^2 + 18x - 9} = 2x - 3$$
.

- 11. Từ các chữ số 0; 1; 2; ...; 9, có thể lập được tất cả bao nhiều số tự nhiên nhỏ hơn 1 000, chia hết cho 5 và gồm các chữ số khác nhau?
- 12. Viết khai triển nhị thức Newton của  $(2x-1)^n$ , biết n là số tự nhiên thoả mãn  $A_n^2 + 24C_n^1 = 140$ .
- 13. Từ các công thức tính diện tích tam giác đã được học, hãy chứng minh rằng, trong tam giác ABC, ta có

$$r = \frac{\sqrt{(b+c-a)(c+a-b)(a+b-c)}}{2\sqrt{a+b+c}}.$$

- 14. Cho hình vuông ABCD có cạnh bằng a. Gọi M, N tương ứng là trung điểm của các cạnh AB, BC.
  - a) Biểu thị các vector  $\overrightarrow{DM}$ ,  $\overrightarrow{AN}$  theo các vector  $\overrightarrow{AB}$ ,  $\overrightarrow{AD}$ .
  - b) Tính  $\overrightarrow{DM} \cdot \overrightarrow{AN}$  và tìm góc giữa hai đường thẳng DM và AN.
- 15. Trong mặt phẳng toạ độ, cho tam giác ABC có ba đỉnh A(-1; 3), B(1; 2), C(4; -2).
  - a) Viết phương trình đường thẳng BC.
  - b) Tính diện tích tam giác ABC.
  - c) Viết phương trình đường tròn có tâm A và tiếp xúc với đường thẳng BC.
- 16. Trên mặt phẳng toạ độ, hai vật thể khởi hành cùng lúc tại hai địa điểm A(1; 1) và B(-1; 21) với các vectơ vận tốc tương ứng là  $\overrightarrow{v_A} = (1; 2)$ ,  $\overrightarrow{v_B} = (1; -4)$ . Hỏi hai vật thể đó có gặp nhau hay không?

- 17. Trong đêm, một âm thanh cầu cứu phát ra từ một vị trí trong rừng và đã được hai trạm ghi tín hiệu ở các vị trí *A*, *B* nhận được. Khoảng cách giữa hai trạm là 16 km và trạm ở vị trí *A* nhận được tín hiệu sớm hơn 6 giây so với trạm ở vị trí *B*. Giả sử vận tốc âm thanh là 1 236 km/h. Hấy xác định phạm vi tìm kiếm vị trí phát ra âm thanh đó.
- 18. Các nhà toán học cổ đại Trung Quốc đã dùng phân số  $\frac{22}{7}$  để xấp xỉ cho  $\pi$ .
  - a) Cho biết đâu là số đúng, đâu là số gần đúng.
  - b) Đánh giá sai số tuyệt đối, sai số tương đối của giá trị gần đúng này, biết

$$3,1415 < \pi < 3,1416$$
.

19. Tỉ lệ hộ nghèo (%) của 10 tỉnh/thành phố thuộc đồng bằng sông Hồng trong năm 2010 và năm 2016 được cho trong bảng sau:

| Tinh/ thành phố  | Năm 2010 | Năm 2016 |
|------------------|----------|----------|
| Hà Nội           | 5,3      | 1,3      |
| <b>Vĩnh</b> Phúc | 10,4     | 2,9      |
| Bắc Ninh         | 7,0      | 1,6      |
| Hải Dương        | 10,8     | 2,3      |
| Hải Phòng        | 6,5      | 2,1      |
| Hưng Yên         | 11,1     | 2,6      |
| Thái Bình        | 10,7     | 3,7      |
| Hà Nam           | 12,0     | 4,4      |
| Nam Định         | 10,0     | 3,0      |
| Ninh Bình        | 12,2     | 4,3      |

(Theo Tổng cục Thống kê)

- a) Tính số trung bình và độ lệch chuẩn của tỉ lệ hộ nghèo các tỉnh/thành phố thuộc đồng bằng sông Hồng trong các năm 2010, 2016.
- b) Dựa trên kết quả nhận được, em có nhận xét gì về số trung bình và độ phân tán của tỉ lệ hộ nghèo các tỉnh/thành phố thuộc đồng bằng sông Hồng trong các năm 2010 và 2016.
- 20. Chọn ngẫu nhiên ba số khác nhau từ 23 số nguyên dương đầu tiên. Tìm xác suất để tổng ba số chọn được là một số chẵn.

# BẢNG TRA CỨU THUẬT NGỮ

Bất phương trình bậc hai một ẩn 22
 Biến cố (là tập con của không gian mẫu) 78
 Biến cố đối 79
 Biến số 6

C Chỉnh hợp 67

Công thức tính khoảng cách từ một điểm đến một đường thẳng 40

Công thức tính góc giữa hai đường thẳng 38

Định nghĩa cổ điển của xác suất 80 Đồ thị của hàm số 7 Đường chuẩn của parabol 52 Đường conic 48

E Elip 49

G Góc giữa hai đường thẳng 37

**H** Hàm số 6

Hàm số bậc hai 11
Hàm số bậc nhất trên từng khoảng 7

Hàm số cho bằng bảng 6

Hàm số cho bằng biểu đồ 6

Hàm số cho bằng công thức 6

Hàm số đồng biến 8

Hàm số nghịch biến 8

Hoán vị 66

Hypebol 50

N Nguyên lí xác suất bé 81
Nhi thức Newton 72

Phương pháp tổ hợp 83 Phương trình chính tắc của elip 49 Phương trình chính tắc của hypebol 51
Phương trình chính tắc của parabol 53
Phương trình đường tròn 43
Phương trình tham số của đường thẳng 34
Phương trình tổng quát của đường thẳng 32

Quy tắc cộng 61Quy tắc nhân 63

Sơ đồ hình cây 61

Tam thức bậc hai 19

Tập giá trị (của hàm số) 6

Tập xác định (của hàm số) 6

Tham số tiêu của parabol 52

Tiêu điểm của parabol 52

Tiêu điểm, tiêu cự của elip 49

Tiêu điểm, tiêu cự của hypebol 50

Tính chất cơ bản của xác suất 80

Tính chất quang học của các đường conic 54

Tổ hợp 68

Vecto chỉ phương của đường thẳng <mark>32</mark>

Vecto pháp tuyến của đường thẳng 31

Vị trí tương đối giữa hai đường thẳng 36

X Xác suất của biến cố đối 85

# BẢNG GIẢI THÍCH THUẬT NGỮ

| Thuật ngữ                                     | Giải thích                                                                                                                                                                            |  |  |  |
|-----------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--|--|--|
| Biến cố đối                                   | Biến cố đối của biến cố <i>E</i> là biến cố xảy ra khi và chỉ khi <i>E</i> không xảy ra.                                                                                              |  |  |  |
| Định lí về dấu của tam<br>thức bậc hai        | Định lí cho phép xác định dấu của tam thức bậc hai $f(x) = ax^2 + bx + c$ tuỳ theo dấu của hệ số $a$ và biệt thức $\Delta$ của nó.                                                    |  |  |  |
| Định nghĩa cổ điển của<br>xác suất            | Xác suất của biến cố E bằng tỉ số giữa số kết quả thuận lợi<br>cho E và tổng số kết quả có thể.                                                                                       |  |  |  |
| Giải một phương trình                         | Tìm tất cả các nghiệm của nó (nghĩa là tìm tập hợp nghiệm).                                                                                                                           |  |  |  |
| Hai phương trình tương<br>đương               | Hai phương trình có cùng tập hợp nghiệm.                                                                                                                                              |  |  |  |
| Nguyên lí xác suất bé                         | Nếu một biến cố có xác suất rất bé thì trong một phép thử<br>biến cố đó sẽ không xảy ra.                                                                                              |  |  |  |
| Phép biến đổi tương<br>đương một phương trình | Phép biến đổi phương trình đó thành một phương trình<br>tương đương.                                                                                                                  |  |  |  |
| Phương pháp toạ độ<br>trong mặt phẳng         | Đưa vào mặt phẳng một hệ trục toạ độ và chuyển các đối tượng hình học sang đối tượng đại số tương ứng, từ đó dùng phương pháp và ngôn ngữ đại số để giải quyết các bài toán hình học. |  |  |  |
| Phương pháp tổ hợp                            | Sử dụng các quy tắc đếm, các công thức tính số hoán vị,<br>chỉnh hợp và tổ hợp để tính số phần tử của không gian<br>mẫu, của các biến cố.                                             |  |  |  |
| Phương trình một ẩn x                         | Mệnh đề chứa biến có dạng $f(x) = g(x)$ , trong đó $f(x)$ và $g(x)$ là những biểu thức của $x$ .                                                                                      |  |  |  |
| Xác suất của biến cố đối                      | Tổng xác suất của biến cố <i>E</i> với xác suất của biến cố đối<br>bằng 1.                                                                                                            |  |  |  |
| Xét chiều biến thiên của<br>hàm số            | Tìm các khoảng đồng biến và các khoảng nghịch biến của<br>hàm số.                                                                                                                     |  |  |  |

# Nhà xuất bản Giáo dục Việt Nam xin trân trọng cảm ơn các tác giả có tác phẩm, tư liệu được sử dụng, trích dẫn trong cuốn sách này.

## Chịu trách nhiệm xuất bản:

Chủ tịch Hội đồng Thành viên NGUYỄN ĐỨC THÁI Tổng Giám đốc HOÀNG LÊ BÁCH

## Chịu trách nhiệm nội dung:

Tổng Giám đốc HOÀNG LÊ BÁCH

Biên tập nội dung: HOÀNG VIỆT - LƯU THẾ SƠN

Biên tập mĩ thuật: NGUYỄN BÍCH LA Thiết kế sách: TRẦN ANH MINH Trình bày bìa: NGUYỄN BÍCH LA

Minh hoa: BÙI VIÊT DUY

Sửa bản in: NGUYỄN NGOC TÚ

Chế bản: CÔNG TY CỔ PHẦN MĨ THUẬT VÀ TRUYỀN THÔNG

## Bản quyền © (2021) thuộc Nhà xuất bản Giáo dục Việt Nam.

Xuất bản phẩm đã đăng kí quyền tác giả. Tất cả các phần của nội dung cuốn sách này đều không được sao chép, lưu trữ, chuyển thể dưới bất kì hình thức nào khi chưa có sự cho phép bằng văn bản của Nhà xuất bản Giáo dục Việt Nam.

## TOÁN 10 - TẬP HAI

Mã số: ...

In ... bản, (QĐ ...) khổ 19 x 26,5 cm.

Đơn vị in: ... Đia chỉ: ...

Số ĐKXB: .../CXBIPH/.../GD.

Số QĐXB: .../QĐ - GD - HN ngày ... tháng ... năm ....

In xong và nộp lưu chiểu tháng ... năm 20...

Mã số ISBN: ...

![](_page_101_Picture_0.jpeg)

# BỘ SÁCH GIÁO KHOA LỚP 10 – KẾT NỐI TRI THỰC VỚI CUỘC SỐNG

- 1. Toán 10, tập mô
- 2. Toán 10, tập hai
- 3. Chuyên để học tập Toán 10
- 4. Ngữ văn 10, tấp một
- 5. Ngữ văn 10, tấp hai
- 6. Chuyên để học tập Ngữ văn 10
- 7. Lich sử 10
- 8. Chuyển để học tập Lịch sử 10
- 9. Địa lí 10
- 10. Chuyên để học tập Địa lí 10
- 11. Giáo dục Kinh tế và Pháp luật 10
- 12. Chuyên để học tập Giáo dục Kinh tế và Pháp luật 10
- 13. Vât lí 10
- 14. Chuyên để học tập Vật lí 10
- 15. Hoá học 10
- 16. Chuyên để học tập Hoá học 10
- 17. Sinh học 10
- 18. Chuyên để học tập Sinh học 10
- 19. Công nghệ 10 Thiết kế và Công nghệ
- 20. Chuyên để học tập Công nghệ 10 Thiết kế và Công nghệ
- 21. Công nghệ 10 Công nghệ trống trọt
- 22. Chuyên để học tập Công nghệ 10 Công nghệ trống trọt
- 23. Tin hoc 10

- 24. Chuyên để học tập Tín học 10 Định hướng Tin học ứng dụng
- 25. Chuyên để học tập Tin học 10 Định hướng Khoa học máy tính
- 26. Mĩ thuật 10 Thiết kế mĩ thuật đa phương tiện
- 27. Mǐ thuật 10 Thiết kế đổ hoạ
- 28. Mithuật 10 Thiết kế thời trang
- 29. Mĩ thuật 10 Thiết kế mĩ thuật sân khấu, điện ảnh
- 30. Mĩ thuật 10 Lí luận và lịch sử mĩ thuật
- 31. Mithuật 10 Điệu khắc
- 32. Mĩ thuật 10 Kiến trúc
- 33. Mĩ thuật 10 Hội hoa
- 34. Mĩ thuật 10 Đố hoa (tranh in)
- 35. Mĩ thuật 10 Thiết kế công nghiệp
- 36. Chuyên để học tập Mĩ thuật 10
- 37 Åmnhac 10
- 38. Chuyên để học tập Âm nhạc 10
- 39. Hoạt động trải nghiệm, hướng nghiệp 10
- 40. Giáo duc thể chất 10 Cấu lông
- 41. Giáo duc thể chất 10 Bóng đá
- 42. Giáo dục Quốc phòng và An ninh 10
- 43. Tiếng Anh 10, tập một
- 44. Tiếng Anh 10, tập hai

# Các đơn vị đầu mối phát hành

• Miền Bắc: CTCP Đầu tư và Phát triển Giáo dục Hà Nội

CTCP Sách và Thiết bi Giáo dục miền Bắc

• Miền Trung: CTCP Đầu tư và Phát triển Giáo dục Đà Nẵng

CTCP Sách và Thiết bị Giáo dục miền Trung

• Miền Nam: CTCP Đầu tư và Phát triển Giáo dục Phương Nam

CTCP Sách và Thiết bị Giáo dục miền Nam

• Cửu Long: CTCP Sách và Thiết bị Giáo dục Cửu Long

Sách điện tử: http://hanhtrangso.nxbgd.vn

Kích hoạt để mở học liệu điện tử: Cào lớp nhũ trên tem để nhận mã số. Truy cập http://hanhtrangso.nxbgd.vn và nhập mã số tại biểu tượng chìa khoá.

![](_page_101_Picture_56.jpeg)

Giá: ...... đ