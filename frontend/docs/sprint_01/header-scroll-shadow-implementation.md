# Header 滚动阴影实现

## 功能描述

实现了 ChatGPT 风格的 Header 动态阴影效果：
- Header 固定高度 52px
- 页面顶部时：无边框（透明阴影）
- 滚动后：显示底部阴影分隔线

## 实现方案

### 1. 状态管理

使用 React hooks 监听滚动状态：

```tsx
const [isScrolled, setIsScrolled] = useState(false);
const scrollContainerRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  const scrollContainer = scrollContainerRef.current;
  if (!scrollContainer) return;

  const handleScroll = () => {
    setIsScrolled(scrollContainer.scrollTop > 0);
  };

  scrollContainer.addEventListener("scroll", handleScroll);
  return () => scrollContainer.removeEventListener("scroll", handleScroll);
}, []);
```

### 2. Header 样式

使用 inline style 动态切换 box-shadow：

```tsx
<div
  className="flex-shrink-0 h-[52px] flex items-center justify-center transition-shadow duration-200"
  style={{
    boxShadow: isScrolled
      ? "0 1px 0 rgba(0, 0, 0, 0.1)"
      : "0 1px 0 transparent",
  }}
>
```

**关键点：**
- `h-[52px]`: 固定高度 52px
- `transition-shadow duration-200`: 平滑过渡动画
- `box-shadow`: 使用透明/可见切换，而不是添加/移除

### 3. 布局结构调整

```
Main Content Area
├── Header (52px, 固定在顶部)
│   └── 动态 box-shadow
└── Scrollable Content (flex-1, overflow-y-auto)
    └── ChatExample (居中, max-w-48rem)
```

## 技术细节

### 滚动容器

```tsx
<div
  ref={scrollContainerRef}
  className="flex-1 overflow-y-auto flex justify-center"
>
  <div className="w-full max-w-[48rem]">
    <ChatExample />
  </div>
</div>
```

**说明：**
- 滚动容器在 Header 下方
- 使用 `ref` 绑定以监听滚动事件
- 内容居中，最大宽度 768px

### 阴影效果

**未滚动状态：**
```css
box-shadow: 0 1px 0 transparent;
```

**滚动状态：**
```css
box-shadow: 0 1px 0 rgba(0, 0, 0, 0.1);
```

**过渡动画：**
```css
transition-shadow duration-200
```
- 200ms 的平滑过渡
- 避免突兀的视觉变化

## 用户体验

### 视觉反馈
- ✅ 页面顶部时，Header 与内容无缝衔接
- ✅ 滚动时，阴影提示用户当前不在顶部
- ✅ 平滑的过渡动画，体验流畅

### 性能优化
- ✅ 使用 `scrollTop > 0` 简单判断，性能开销小
- ✅ 事件监听器在组件卸载时正确清理
- ✅ 避免频繁的 DOM 操作

## 代码对比

### 之前
```tsx
<div className="flex-shrink-0 h-14 border-b border-zinc-200">
  {/* Header 内容 */}
</div>
```

**问题：**
- 固定边框，无论是否滚动都显示
- 高度 56px (h-14)

### 现在
```tsx
<div
  className="flex-shrink-0 h-[52px] transition-shadow duration-200"
  style={{
    boxShadow: isScrolled ? "0 1px 0 rgba(0, 0, 0, 0.1)" : "0 1px 0 transparent",
  }}
>
  {/* Header 内容 */}
</div>
```

**改进：**
- 动态阴影，根据滚动状态显示
- 高度 52px，更符合设计规范
- 平滑过渡动画

## 相关文件

- `/app/chat-ui/page.tsx` - 主要修改文件
  - 添加滚动状态管理
  - 实现动态阴影效果
  - 调整布局结构

## 测试要点

### 功能测试
- [ ] 页面加载时，Header 无阴影
- [ ] 向下滚动时，Header 显示阴影
- [ ] 滚动回顶部时，阴影消失
- [ ] 阴影过渡平滑，无闪烁

### 兼容性测试
- [ ] 不同浏览器下效果一致
- [ ] 移动端触摸滚动正常
- [ ] 快速滚动时状态更新及时

### 性能测试
- [ ] 滚动流畅，无卡顿
- [ ] 内存无泄漏（事件监听器正确清理）
- [ ] CPU 占用正常

## 设计规范

### 尺寸
- Header 高度: `52px`
- 内容最大宽度: `768px` (48rem)

### 颜色
- 阴影颜色: `rgba(0, 0, 0, 0.1)`
- 透明阴影: `transparent`

### 动画
- 过渡时长: `200ms`
- 缓动函数: 默认 (ease)

## 后续优化

1. **节流优化**
   - 使用 throttle 减少滚动事件处理频率
   - 进一步提升性能

2. **更多状态**
   - 根据滚动距离调整阴影深度
   - 添加滚动方向判断

3. **可配置化**
   - 将阴影样式提取为配置项
   - 支持主题定制

4. **无障碍优化**
   - 添加 ARIA 属性
   - 支持键盘导航时的视觉反馈

