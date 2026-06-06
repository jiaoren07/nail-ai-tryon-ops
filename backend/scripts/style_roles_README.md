# style_roles 角色分配说明

每行格式：`<id>: <角色> — <一句话理由>`。基于 [tags_qwen.json](file:///d:/美团AI%20HACKATHON/dataset/styles/tags_qwen.json) 的打标结果与 [implementation-plan.md](../../implementation-plan.md) §1.3 的三条选定原则：

- **stable_hot** — 标签含「经典/极简/通勤/哑光/纯色」等通用关键字
- **emerging_hot** — 视觉辨识度最高、风格鲜明
- **cold** — 风格小众或与主流偏好相反
- **long_tail** — 其余

合计应为 40 行（女 25 + 男 15）。

## 女款（25）

- `f_01: stable_hot — 纯色+极简双关键字命中，复杂度 1 最低，最典型的稳态高频款`
- `f_02: long_tail — 跳色+纯色，介于经典与突出之间，无强记忆点`
- `f_03: long_tail — 复杂图案+跳色，中等冲击但无独特维度`
- `f_04: long_tail — 跳色+闪光，常见花哨组合`
- `f_05: cold — 25 款女款里唯一的 short 长度，与主流偏好（medium/long）相反`
- `f_06: long_tail — 法式+镶钻，标签经典但被 f_13 占了 stable_hot 名额`
- `f_07: long_tail — 渐变+闪光+复杂图案，候选 emerging_hot 但视觉冲击弱于 f_09`
- `f_08: cold — 渐变+镶钻+透明，「透明」标签在女款里属少见维度`
- `f_09: emerging_hot — 跳色+镶钻+复杂图案，三种视觉冲击元素叠加，辨识度最高`
- `f_10: long_tail — 法式+渐变，warm tone，但被 f_14 占了 stable_hot`
- `f_11: cold — 透明+复杂图案，透明与复杂的小众组合`
- `f_12: long_tail — 法式+复杂图案，复杂度 4 偏高`
- `f_13: stable_hot — 法式+镶钻，法式经典 + 镶钻是法式标配`
- `f_14: stable_hot — 法式+渐变，复杂度 2，法式经典款里最"稳"的`
- `f_15: emerging_hot — 复杂图案+跳色+几何 (warm)，25 款里仅 3 款 warm，几何是少见维度`
- `f_16: long_tail — 渐变+闪光+跳色 (warm)，三标签都常见`
- `f_17: long_tail — 镶钻+透明+跳色，三标签常见组合`
- `f_18: long_tail — 镶钻+跳色，常见组合`
- `f_19: long_tail — 镶钻+闪光+透明，常见组合`
- `f_20: long_tail — 镶钻+闪光+透明，与 f_19 同质`
- `f_21: long_tail — 法式+镶钻+闪光，法式但被 f_13/f_14 占名额`
- `f_22: long_tail — 闪光+纯色，复杂度 2，但纯色单标签不足以撑 stable_hot`
- `f_23: long_tail — 法式+镶钻，与 f_13 重复`
- `f_24: long_tail — 闪光+跳色，常见组合`
- `f_25: long_tail — 法式+跳色 (warm)，warm 多样性已由 f_15 体现`

## 男款（15）

- `m_01: stable_hot — 哑光+纯色+商务，三 stable_hot 关键字全命中，复杂度 1 最低`
- `m_02: long_tail — 哑光+纯色+透明+商务，加了「透明」削弱稳态感`
- `m_03: long_tail — 哑光+纯色+商务 (warm)，与 m_01 同 warm 同标签，重复`
- `m_04: long_tail — 哑光+纯色+个性+镶钻，「个性」拉离 stable`
- `m_05: long_tail — 极简+纯色+个性+渐变，极简与个性矛盾`
- `m_06: stable_hot — 哑光+纯色+深色系+商务 (cool)，三关键字全命中 + 加 cool tone 与 m_01 warm 形成稳态对偶`
- `m_07: long_tail — 个性+酷炫+几何+跳色，候选 emerging_hot 但 neutral tone 不如 m_15 跳`
- `m_08: long_tail — 个性+几何+闪光，无 stable 关键字也无极致辨识度`
- `m_09: long_tail — 哑光+纯色+个性+几何，混合特征`
- `m_10: cold — 个性+酷炫+朋克+镶钻，「朋克」标签极小众`
- `m_11: long_tail — 个性+酷炫+几何+闪光，三流行 ops 标签`
- `m_12: long_tail — 哑光+深色系+个性+闪光，混合特征`
- `m_13: cold — 个性+酷炫+朋克，朋克 + 无装饰，更纯粹的小众`
- `m_14: long_tail — 个性+酷炫+几何+镶钻，常见炫款`
- `m_15: emerging_hot — 深色系+个性+酷炫+几何 (cool)，黑色 cool tone + 酷炫几何，男款里视觉最跳`
