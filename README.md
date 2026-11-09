# AI大模型免费资源导航

**站点名：** AI大模型免费资源导航  
**主站（canonical）：** https://aidamoxing-mianfei.netlify.app/  
**GitHub Pages：** https://9499758-wq.github.io/x-yangmao/  

旧域名 `aiyangmao.netlify.app` 已停用（Netlify 站点已重命名）。

## 功能

- 每 6 小时 GitHub Actions 自动抓取 / 中文整理 / 构建 / 提交（零人工）
- 自愈：源失败保留旧数据；翻译不可用（GitHub Models 已于 2026-07 退役）则关键词中文回退；页面永不空
- 深度百度 SEO：首页、分类页、条目详情页、日归档、JSON-LD、sitemap 索引/xml/txt、robots、404
- 可选百度普通收录推送（`BAIDU_PUSH_TOKEN`）

## 百度站长平台（需用户操作）

1. 打开 https://ziyuan.baidu.com 登录
2. 添加站点：`https://aidamoxing-mianfei.netlify.app/`
3. 完成验证（HTML 标签或文件）。把验证码写入仓库：
   - Actions Secret `VERIFY_BAIDU`，或
   - `seo_config.json` 的 `baidu_site_verification`
4. 提交 sitemap：`https://aidamoxing-mianfei.netlify.app/sitemap_index.xml`
5. 在站长平台创建「普通收录」推送 token，添加为仓库 Secret `BAIDU_PUSH_TOKEN`（可选，有则 Actions 自动推送）
6. **本仓库不会代为提交百度站长**——需你自己的百度账号完成以上步骤

## 本地

```bash
python3 fetch_auto.py
python3 build.py
```
