# 故障排除指南

## 常见错误及解决方案

### 1. Module not found: Can't resolve '@/components/ui/sonner'

**错误信息：**
```
Module not found: Can't resolve '@/components/ui/sonner'
```

**解决方案：**
✅ 已修复！`components/ui/sonner.tsx` 文件已创建。

---

### 2. Module not found: Can't resolve '@/components/ui/tabs'

**错误信息：**
```
Module not found: Can't resolve '@/components/ui/tabs'
```

**解决方案：**
✅ 已修复！`components/ui/tabs.tsx` 文件已创建。

---

### 3. 后端连接失败

**错误信息：**
```
Backend request failed
```

**解决方案：**
1. 检查后端是否启动：
   ```bash
   curl http://localhost:8000/health
   ```

2. 检查环境变量：
   ```bash
   cat .env.local
   # 应该包含：
   # NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. 启动后端：
   ```bash
   cd ../backend
   ./start_server.sh
   ```

---

### 4. 依赖安装失败

**错误信息：**
```
pnpm install failed
```

**解决方案：**
```bash
# 清除缓存
rm -rf node_modules .next pnpm-lock.yaml

# 重新安装
pnpm install
```

---

### 5. 端口被占用

**错误信息：**
```
Port 3000 is already in use
```

**解决方案：**
```bash
# 方式 1：使用其他端口
pnpm dev -- -p 3001

# 方式 2：杀掉占用端口的进程
lsof -ti:3000 | xargs kill -9
```

---

### 6. TypeScript 类型错误

**错误信息：**
```
Type error: ...
```

**解决方案：**
```bash
# 重新生成类型
pnpm run build

# 或者重启 TypeScript 服务器（在 VSCode 中）
# Cmd/Ctrl + Shift + P -> "TypeScript: Restart TS Server"
```

---

### 7. AI Elements 组件不显示

**问题：** 某些 AI Elements 组件不渲染

**解决方案：**
1. 检查组件是否存在：
   ```bash
   ls components/ai-elements/
   ```

2. 如果缺失，重新安装：
   ```bash
   npx ai-elements@latest
   ```

3. 检查导入路径：
   ```typescript
   // 正确
   import { Message } from "@/components/ai-elements/message"
   
   // 错误
   import { Message } from "ai-elements"
   ```

---

### 8. 流式输出不工作

**问题：** 消息一次性显示，没有流式效果

**可能原因和解决方案：**

1. **后端不支持 SSE**
   - 检查后端 `/chat` 接口是否返回 `text/event-stream`
   - 确保后端设置了 `stream: true`

2. **Edge Runtime 未启用**
   - 检查 `app/api/chat/route.ts` 是否有：
     ```typescript
     export const runtime = 'edge';
     ```

3. **浏览器不支持**
   - 确保使用现代浏览器（Chrome, Firefox, Safari, Edge）
   - 检查浏览器控制台是否有错误

---

### 9. 会话不保存

**问题：** 刷新页面后会话丢失

**解决方案：**
1. 检查浏览器是否禁用 localStorage：
   ```javascript
   // 在浏览器控制台运行
   localStorage.setItem('test', 'test')
   console.log(localStorage.getItem('test'))
   ```

2. 检查是否在隐私模式：
   - 隐私模式下 localStorage 可能不可用

3. 清除浏览器缓存后重试

---

### 10. 环境变量不生效

**问题：** 修改 `.env.local` 后没有效果

**解决方案：**
1. 重启开发服务器：
   ```bash
   # 停止当前服务器（Ctrl+C）
   # 重新启动
   pnpm dev
   ```

2. 确保变量名以 `NEXT_PUBLIC_` 开头（如果在客户端使用）：
   ```bash
   # 正确（客户端可用）
   NEXT_PUBLIC_API_URL=http://localhost:8000
   
   # 错误（仅服务器端可用）
   API_URL=http://localhost:8000
   ```

---

## 开发调试技巧

### 1. 查看网络请求

打开浏览器开发者工具：
- **Network** 标签
- 筛选 `Fetch/XHR`
- 查看 `/api/chat` 请求
- 检查请求头、请求体、响应

### 2. 查看控制台日志

```typescript
// 在组件中添加调试日志
console.log('Messages:', messages)
console.log('Current mode:', mode)
console.log('Session:', currentSession)
```

### 3. 使用 React DevTools

安装 React DevTools 浏览器扩展：
- 查看组件树
- 检查 props 和 state
- 查看 Context 值

### 4. 查看后端日志

```bash
cd backend
tail -f logs/app.log
```

---

## 性能优化

### 1. 消息过多导致卡顿

**解决方案：**
- 实现消息虚拟滚动
- 限制显示的消息数量
- 使用分页加载

### 2. 图片加载慢

**解决方案：**
- 使用 Next.js Image 组件
- 启用图片懒加载
- 压缩图片大小

### 3. 代码高亮性能问题

**解决方案：**
- 使用 Web Worker 进行高亮
- 限制高亮的代码长度
- 使用轻量级高亮库

---

## 获取帮助

如果以上方案都无法解决问题：

1. **查看文档：**
   - [Sprint 1 完成总结](./docs/sprint_01/SPRINT1_COMPLETION.md)
   - [快速开始指南](./docs/sprint_01/QUICKSTART.md)
   - [AI Elements 使用说明](./docs/sprint_01/AI_ELEMENTS_USAGE.md)

2. **查看官方文档：**
   - [Next.js 文档](https://nextjs.org/docs)
   - [AI SDK 文档](https://v6.ai-sdk.dev/docs)
   - [AI Elements 文档](https://v6.ai-sdk.dev/elements)

3. **检查日志：**
   - 浏览器控制台
   - 终端输出
   - 后端日志文件

4. **提交 Issue：**
   - 描述问题
   - 提供错误信息
   - 附上相关代码

---

## 快速检查清单

启动前检查：
- [ ] 已安装依赖（`pnpm install`）
- [ ] 已创建 `.env.local` 文件
- [ ] 后端服务已启动
- [ ] 端口 3000 未被占用

运行时检查：
- [ ] 浏览器控制台无错误
- [ ] 网络请求正常
- [ ] 后端日志无错误
- [ ] localStorage 可用

---

**最后更新：** 2025-11-11  
**版本：** Sprint 1 (v0.1.0)

