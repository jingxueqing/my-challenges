# C4C 作业求解验证报告

- 生成时间：2026-10-07 15:51:30
- 题目总数：**12**
- 自动解出：**10**（83.3%）
- 通过自动验证：**9**
- 验证失败：**0**
- 推理后端：`none`（未配置 key，降级为 local 确定性后端）

## 路由分布

| 路径 | 题数 |
|------|------|
| `sympy` | 10 |
| `none` | 2 |

## 逐题明细

| 题号 | 求解 | 路径 | 验证 | 答案摘要 |
|------|------|------|------|----------|
| 1 | ✅ | `sympy` | ✅ pass | \det(A) = 10;\quad \operatorname{rank}(A) = 2 |
| 2 | ✅ | `sympy` | ✅ pass | P^{-1}AP = D = \left[\begin{matrix}1 & 0\\0 & 3\end{ |
| 3 | ✅ | `sympy` | ✅ pass | \left[\begin{matrix}- \frac{1}{3} & \frac{2}{3}\\\fr |
| 4 | ✅ | `sympy` | ✅ pass | \text{线性相关} |
| 5 | ✅ | `sympy` | ✅ pass | y{\left(x \right)} = C_{1} e^{- 2 x} |
| 6 | ✅ | `sympy` | ✅ pass | y{\left(x \right)} = C_{1} \sin{\left(x \right)} + C |
| 7 | ✅ | `sympy` | ✅ pass | a = 5\,\mathrm{m/s^2} |
| 8 | ✅ | `sympy` | ✅ pass | I = 4\,\mathrm{A} |
| 9 | ✅ | `sympy` | – unverified | F = 53940000000\,\mathrm{N} |
| 10 | ✅ | `sympy` | ✅ pass | t = 3.03\,\mathrm{s},\quad v = 29.7\,\mathrm{m/s} |
| 11 | ❌ | `none` | – unverified | LLM 已禁用，且该题不属确定性题库 |
| 12 | ❌ | `none` | – unverified | LLM 已禁用，且该题不属确定性题库 |

## 验证证据

### Problem 1 — pass

- ✓ **det-秩一致性**：det(A) = 10，rank(A) = 2，2×2（三者一致）

### Problem 2 — pass

- ✓ **特征对验证**：Av − λv = 0，特征对成立
- ✓ **特征对验证**：Av − λv = 0，特征对成立
- ✓ **特征值-迹自洽**：Σλ = 4，tr(A) = 4

### Problem 3 — pass

- ✓ **逆矩阵验证**：AA⁻¹ = \left[\begin{matrix}1 & 0\\0 & 1\end{matrix}\right]
- ✓ **逆矩阵验证**：AA⁻¹ = \left[\begin{matrix}1 & 0\\0 & 1\end{matrix}\right]，等于单位阵

### Problem 4 — pass

- ✗ **线性相关性**：rank=2，向量数=3
- ✓ **线性相关性**：3 个向量，rank = 2，存在非平凡零组合 \left[\begin{matrix}-2 & 1 & 0\end{matrix}\right]⟹线性相关

### Problem 5 — pass

- ✓ **残差验证**：残差 = 0

### Problem 6 — pass

- ✓ **残差验证**：残差 = 0

### Problem 7 — pass

- ✓ **量纲齐次性**：公式 N = kg·m/s^2 两侧量纲一致

### Problem 8 — pass

- ✓ **量纲齐次性**：公式 I = V/R 两侧量纲一致

### Problem 10 — pass

- ✓ **量纲齐次性**：公式 h = \frac{1}{2} g t^2 两侧量纲一致
