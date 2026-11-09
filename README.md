# AI大模型免费资源导航

站点：**AI大模型免费资源导航**  
关键词：大模型免费API · AI工具免费 · GitHub热门项目

## 线上地址

- Netlify（主站 / 百度 canonical）：https://aidamoxing-mianfei.netlify.app/
- GitHub Pages：https://9499758-wq.github.io/x-yangmao/

旧域名 `aiyangmao.netlify.app` 已停用（站点已重命名）。

## 全自动更新

GitHub Actions 每 6 小时：`fetch_auto.py` → Models 批量中文翻译（失败则关键词回退）→ `build.py` 生成首页 / 日归档 / sitemap / robots → 自动 commit。

自愈策略：某源失败保留旧数据；翻译失败不阻断构建；页面永不空。

## 本地

```bash
python3 fetch_auto.py
python3 build.py
```
