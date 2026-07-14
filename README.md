# 3Dcer_to_2D
3D Cartesian Blade-Section to 2D Coordinate Converter

该程序用于将叶片截面的三维 Cartesian 坐标转换为多种二维坐标。
程序支持一次处理一个或多个截面，可输出有量纲弧长坐标和 MISES 叶栅坐标.

主程序入口：

```text
3Dcor_2_2Dcor.py
```

## 1. 主要功能

- 读取 AutoGrid5 `.geomTurbo` 多截面叶型。
- 读取带叶片数、吸力面和压力面标签的单截面 XYZ 文本。
- 将每侧三维曲线按弧长余弦分布重采样。
- 输出 MISES `(m', theta)` 坐标和 `stream.*` 文件。
- 输出有量纲子午/周向坐标 `(s, u)`。
- 可将前缘到尾缘的弦线刚体旋转到 x 轴。
- 可将旋转后的叶型等比例缩放到单位弦长。
- 可根据运行工况生成每个截面的 MISES `ises.*` 边界条件。
- 检查前缘、尾缘闭合以及二维轮廓自交。


## 2. 环境要求

- Python 3.10 或更高版本。
- NumPy 1.24 或更高版本。
- matplotlib 3.7 或更高版本。

在项目目录安装依赖：

```bash
python -m pip install -r requirements.txt
```

## 3. 快速开始

### 3.1 转换 geomTurbo 多截面文件

```bash
python 3Dcor_2_2Dcor.py \
  'input.geomTurbo' \
  --input-format geomturbo \
  --output-dir results/case \
  --case case \
  --plot save
```

`geomturbo` 是默认输入格式，因此 `--input-format geomturbo` 可以省略。

### 3.2 转换单截面 XYZ 文件

```bash
python 3Dcor_2_2Dcor.py hpc21a_s1.dat \
  --input-format xyz \
  --output-dir results/hpc21a_s1 \
  --case hpc21a_s1 \
  --normalize-chord \
  --plot save
```

### 3.3 同时生成 MISES 边界条件

```bash
python 3Dcor_2_2Dcor.py input.geomTurbo \
  --output-dir results/case \
  --case case \
  --operating-condition operating_condition.example \
  --plot save
```

实际保存目录的绝对路径为：

```text
Results saved to: /absolute/path/to/results/case
```

## 4. 输入文件

### 4.1 geomTurbo 格式

使用：

```bash
--input-format geomturbo
```

geomturbo文件可从 AG5中导出，程序从文件中读取：

- `PERIODICITY`：叶片数；
- `SUCTION / SECTIONAL`：吸力面截面块；
- `PRESSURE / SECTIONAL`：压力面截面块；
- `SECTIONAL` 下一行：截面总数；
- 每个 `XYZ` 标记后的整数：该截面的坐标点数；
- 后续各行：`x y z` 三维坐标。

吸力面和压力面的截面数量必须相同。每个截面中，两侧点都应按照前缘到尾缘的
方向排列。程序会按出现顺序将两侧截面配对并编号为 `1, 2, ...`。

geomTurbo 文件必须包含有效的正整数叶片数，否则程序会停止。

### 4.2 单截面 XYZ 文本

使用：

```bash
--input-format xyz
```

文件结构如下：

```text
36
suction
x1 y1 z1
x2 y2 z2
...
pressure
x1 y1 z1
x2 y2 z2
...
```

要求：

- 第一个非空、非注释行必须是正整数叶片数。
- `suction` 后写吸力面坐标。
- `pressure` 后写压力面坐标。

XYZ 文本只表示一个截面，输出截面编号固定为 1。


## 5. 坐标约定

输入笛卡尔坐标记为 `(x, y, z)`：

- `z` 为轴向坐标；
- `r = sqrt(x^2 + y^2)` 为径向半径；
- `theta = atan2(y, x)` 为周向角。

程序会对 `theta` 进行连续展开，避免曲线穿过 `-pi / pi` 时出现角度跳变。

输入长度单位可以是毫米、米或其他一致单位。几何坐标输出默认沿用输入长度单位；
只有 MISES 工况计算会通过 `length_scale` 将输入几何单位转换为米。

## 6. 重采样

每个表面首先按三维折线弧长参数化，再使用余弦分布重采样为 N 点：

```text
q_i = 0.5 * [1 - cos(i*pi/(N-1))]
N = 201
```

余弦分布会在前缘和尾缘附近布置更多点。坐标值使用弧长参数上的一维插值得到。
连续重复点会自动合并。

## 7. MISES 二维坐标 `(m', theta)`

输出文件：

```text
blade.<case>_section_NN
stream.<case>_section_NN
```

子午面微元为：

```text
dm = sqrt(dz^2 + dr^2)
```

MISES 流向坐标按每个折线段的平均半径积分：

```text
dm' = dm / r_avg
m'  = integral(dm')
```

吸力面和压力面分别积分。为消除两侧离散积分带来的尾缘微小差异，两侧终点统一到
平均尾缘值，并在各自表面内部按流向位置施加线性修正：

```text
m'_TE = (m'_TE,suction + m'_TE,pressure) / 2
```

该修正保持前缘不动，只消除公共尾缘的数值间隙。

`blade.*` 中的主要坐标列为：

```text
m'  theta
```

文件头同时保存入口斜率、出口斜率、子午弦长和叶栅节距。`stream.*` 保存计算域
入口、叶片前缘、叶片尾缘和出口处的流道参考信息。

## 8. 有量纲弧长坐标 `(s, u)`

每个截面都会生成：

```text
blade_su.<case>_section_NN
```

第一坐标是每侧在 `(z, r)` 子午面中的弧长：

```text
ds = sqrt(dz^2 + dr^2)
s  = integral(ds)
```

吸力面和压力面使用各自的几何分别积分，程序将两侧尾缘弧长调整到共同平均值：

```text
s_TE = (s_TE,suction + s_TE,pressure) / 2
s_new = s_old + (s_TE - s_old,TE) * (s_old - s_LE) / (s_old,TE - s_LE)
```

第二坐标是固定子午位置上的局部周向圆弧长度：

```text
theta_ref = (theta_LE,suction + theta_LE,pressure) / 2
u = r(s) * [theta(s) - theta_ref]
```

`s` 和 `u` 与输入 XYZ 使用相同的长度单位。

需要注意：当半径随流向变化时，`(s, u)` 是便于观察长度的工程坐标，并不是旋转
曲面的严格等距展开。旋转曲面的线元为：

```text
dl^2 = ds^2 + r(s)^2 dtheta^2
```

因此在径向变化较大的截面上，`(s, u)` 外观与共形的 `(m', theta)` 坐标可能明显不同。

## 9. 弦线对齐坐标 `(x, y)`

启用：

```bash
--align-su-chord
```

额外输出：

```text
blade_xy.<case>_section_NN
```

程序以公共前缘为原点，并取两侧公共尾缘位置，计算：

```text
delta_s = s_TE - s_LE
delta_u = u_TE - u_LE
alpha = atan2(delta_u, delta_s)
c = sqrt(delta_s^2 + delta_u^2)
```

所有点绕前缘刚体旋转 `-alpha`：

```text
x =  delta_s_point*cos(alpha) + delta_u_point*sin(alpha)
y = -delta_s_point*sin(alpha) + delta_u_point*cos(alpha)
```

旋转后：

```text
LE = (0, 0)
TE = (c, 0)
```

## 10. 单位弦长坐标 `(x/c, y/c)`

启用：

```bash
--normalize-chord
```

该选项会自动执行弦线对齐，无需同时填写 `--align-su-chord`。额外输出：

```text
blade_xyn.<case>_section_NN
<case>_normalization_summary.csv
```

旋转后的所有坐标使用同一个比例缩放：

```text
x_normalized = x / c
y_normalized = y / c
```

结果满足：

```text
LE = (0, 0)
TE = (1, 0)
```

`blade_xyn.*` 保存完整、未切削的闭合轮廓，包含前缘和尾缘。归一化汇总 CSV 包含：

- 截面编号；
- 旋转角，单位 rad 和 degree；
- 原始弦长；
- 缩放因子；
- 前缘和尾缘坐标；
- 归一化后的坐标范围；
- 每侧点数。

## 11. 尾缘切削参数 `ndel`

默认值：

```text
吸力面 7 点
压力面 7 点
```

命令行修改示例：

```bash
--ndel 5 6
```

第一个整数对应吸力面，第二个整数对应压力面。每侧必须至少保留两个点。

`blade_xyn.*` 始终保存完整未切削轮廓，便于几何检查和后续处理。

## 12. MISES 边界条件

通过以下参数提供工况文件：

```bash
--operating-condition operating_condition.dat
```


推荐使用带字段名的格式：

```text
length_scale = 0.01
rpm = 17188.0
inlet_total_pressure = 100000.0
inlet_total_temperature = 293.0
inlet_absolute_angle = 0.0
outlet_static_pressure = 140000.0
```

也支持一行六个数字，顺序必须为：

```text
length_scale rpm inlet_total_pressure inlet_total_temperature inlet_absolute_angle outlet_static_pressure
```

字段说明：

| 字段 | 含义 | 单位 |
| --- | --- | --- |
| `length_scale` | 输入几何长度到米的缩放系数 | m / 输入长度单位 |
| `rpm` | 转速 | rpm |
| `inlet_total_pressure` | 入口总压 | Pa |
| `inlet_total_temperature` | 入口总温 | K |
| `inlet_absolute_angle` | 入口绝对流角 | degree |
| `outlet_static_pressure` | 出口静压 | Pa |

计算采用理想空气：

```text
gamma = 1.4
R = 287 J/(kg*K)
```

程序根据截面进出口半径、转速、压力和温度计算速度三角形，通过质量流量和相对总焓
关系迭代出口速度，并计算相对马赫数、出口压比和雷诺数。

每个截面输出：

```text
ises.<case>_section_NN
```

整个算例还会输出：

```text
<case>_ises_summary.csv
```

汇总文件包含输入工况和以下派生结果：

- 入口流态；
- 入口相对马赫数；
- 出口相对马赫数；
- 出口静压与入口相对总压之比；
- 入口和出口流向斜率；
- 入口和出口计算平面位置；
- 雷诺数；
- 迭代次数。

工况文件中的数值必须与当前几何和截面位置匹配。如果计算得到非正的出口相对动能，
程序会停止，并提示检查 `length_scale`、转速、压力和温度。

## 13. 绘图

单截面图片：

| 文件 | 内容 |
| --- | --- |
| `<case>_section_NN_check.png` | MISES `(m', theta)`，显示切削前后轮廓 |
| `<case>_section_NN_su_check.png` | 有量纲 `(s, u)`，显示切削前后轮廓 |
| `<case>_section_NN_xy_check.png` | 弦线对齐坐标，仅启用对齐或归一化时生成 |
| `<case>_section_NN_xyn_check.png` | 单位弦长坐标，仅启用归一化时生成 |

多截面且使用 `--plot save` 时还会生成：

```text
<case>_overview.png
<case>_su_overview.png
<case>_xy_overview.png
<case>_xyn_overview.png
```

## 14. 输出文件汇总

假设算例名为 `case`，截面编号为 1：

| 文件 | 是否默认生成 | 内容 |
| --- | --- | --- |
| `blade.case_section_01` | 是 | MISES 切削叶型 `(m', theta)` |
| `stream.case_section_01` | 是 | MISES 流道参考信息 |
| `blade_su.case_section_01` | 是 | 有量纲切削叶型 `(s, u)` |
| `blade_xy.case_section_01` | 可选 | 弦线对齐的切削叶型 |
| `blade_xyn.case_section_01` | 可选 | 完整单位弦长轮廓 |
| `ises.case_section_01` | 可选 | MISES 边界条件 |
| `case_normalization_summary.csv` | 可选 | 弦线旋转和归一化信息 |
| `case_ises_summary.csv` | 可选 | 工况输入和派生边界参数 |
| `case_section_01_*.png` | 取决于绘图模式 | 单截面检查图 |
| `case_*_overview.png` | 多截面时可选 | 全部截面总览图 |


## 16. 命令行参数

查看完整帮助：

```bash
python 3Dcor_2_2Dcor.py --help
```

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `input` | 必填 | 输入几何文件路径 |
| `--input-format` | `geomturbo` | `geomturbo`、`xyz` 或 `legacy` |
| `--output-dir` | `output` | 输出目录，不存在时自动创建 |
| `--case` | 输入文件名 | 输出文件的算例前缀 |
| `--ndel SUCTION PRESSURE` | `7 7` | 两侧尾缘切削点数 |
| `--operating-condition` | 无 | MISES 工况文件 |
| `--opr` | 无 | `--operating-condition` 的简写 |
| `--plot` | `save` | `save`、`show` 或 `none` |
| `--align-su-chord` | 关闭 | 生成弦线对齐坐标 |
| `--normalize-chord` | 关闭 | 生成单位弦长坐标，并自动对齐弦线 |
| `--legacy` | 关闭 | 等价于 `--input-format legacy` |


