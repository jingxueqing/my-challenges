# 线性代数与常微分方程 — 习题 7

> 姓名：JingXueQing　　学号：2024102110351　　日期：2026-10-06
>
> 本次作业覆盖：矩阵运算、特征值与对角化、线性相关性、
> 一阶与二阶常微分方程、牛顿运动定律与电路分析。

---

## Problem 1

设矩阵

$$A = \begin{bmatrix} 4 & 1 \\ 2 & 3 \end{bmatrix}$$

求 $A$ 的行列式 $\det(A)$ 与秩 $\operatorname{rank}(A)$，并判断 $A$ 是否可逆。

---

## Problem 2

设

$$A = \begin{bmatrix} 2 & 1 \\ 1 & 2 \end{bmatrix}$$

求 $A$ 的全部特征值与对应特征向量，并判断 $A$ 是否可以对角化。

---

## Problem 3

求矩阵

$$B = \begin{bmatrix} 1 & 2 \\ 2 & 1 \end{bmatrix}$$

的逆矩阵 $B^{-1}$，并验证 $BB^{-1} = I$。

---

## Problem 4

判断向量组

$$\mathbf{v}_1 = \begin{bmatrix} 1 \\ 2 \\ 3 \end{bmatrix}, \quad
  \mathbf{v}_2 = \begin{bmatrix} 2 \\ 4 \\ 6 \end{bmatrix}, \quad
  \mathbf{v}_3 = \begin{bmatrix} 1 \\ 0 \\ 1 \end{bmatrix}$$

是否线性无关，并说明理由。

---

## Problem 5

解一阶常微分方程

$$y' + 2y = 0$$

求其通解。

---

## Problem 6

解二阶常系数齐次线性微分方程

$$y'' + y = 0$$

求其通解。

---

## Problem 7

一质量为 $2\,\mathrm{kg}$ 的物体受到合力 $F = 10\,\mathrm{N}$ 的作用，
求该物体的加速度 $a$（用牛顿第二定律）。

---

## Problem 8

电路中电压 $U = 220\,\mathrm{V}$ 加在电阻 $R = 55\,\mathrm{ohm}$ 两端，
求通过电阻的电流 $I$（用欧姆定律）。

---

## Problem 9

两个点电荷 $q_1 = 2\,\mathrm{C}$ 与 $q_2 = 3\,\mathrm{C}$ 相距 $r = 1\,\mathrm{m}$，
求它们之间的库仑力大小。

---

## Problem 10

一个物体从 $h = 45\,\mathrm{m}$ 高处自由落下，
求它落地所需的时间与落地速度（取 $g = 9.8\,\mathrm{m/s^2}$）。

---

## Problem 11

（超出当前求解器支持范围，用于测试诚实失败行为）
请证明：对任意 $n \times n$ 可逆矩阵 $A$，其特征值均不为零。

---

## Problem 12

设某区间上的分段函数为

$$f(x) = \begin{cases} x^2 & x < 0 \\ -x & x \ge 0 \end{cases}$$

求 $\lim_{x \to 0} f(x)$，并判断 $f$ 在 $x = 0$ 处是否连续。