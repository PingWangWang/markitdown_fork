# 同步上游仓库更新指南

本文档说明如何将原始 MarkItDown 仓库（https://github.com/microsoft/markitdown.git）的更新同步到您的 fork 分支。

## 前置条件

确保您已经：

1. Fork 了原始仓库到您的 GitHub 账户
2. 克隆了您的 fork 到本地

## 配置步骤

### 1. 添加上游远程仓库（首次设置只需执行一次）

```bash
# 查看当前远程仓库
git remote -v

# 添加上游远程仓库（original repository）
git remote add upstream https://github.com/microsoft/markitdown.git

# 验证添加成功
git remote -v
```

您应该看到类似输出：

```
origin    https://github.com/你的用户名/markitdown.git (fetch)
origin    https://github.com/你的用户名/markitdown.git (push)
upstream  https://github.com/microsoft/markitdown.git (fetch)
upstream  https://github.com/microsoft/markitdown.git (push)
```

### 2. 同步更新的常规流程

每次需要同步上游更新时，按以下步骤操作：

#### 方法一：使用 rebase（推荐，保持提交历史整洁）

```bash
# 1. 切换到主分支
git checkout main

# 2. 获取上游最新更改
git fetch upstream

# 3. 将上游更改变基到本地分支
git rebase upstream/main

# 4. 如果有冲突，解决冲突后继续
git rebase --continue

# 5. 推送到您的 fork（可能需要强制推送）
git push origin main
# 如果提示需要强制推送
git push --force-with-lease origin main
```

#### 方法二：使用 merge（保留合并记录）

```bash
# 1. 切换到主分支
git checkout main

# 2. 获取上游最新更改
git fetch upstream

# 3. 合并上游更改到本地分支
git merge upstream/main

# 4. 如果有冲突，解决冲突后提交
git commit

# 5. 推送到您的 fork
git push origin main
```

### 3. 处理冲突

如果在 rebase 或 merge 过程中出现冲突：

```bash
# 查看冲突文件
git status

# 手动编辑冲突文件，解决冲突标记（<<<<<<<, =======, >>>>>>>）

# 标记冲突已解决
git add <冲突文件>

# 继续 rebase（如果使用 rebase）
git rebase --continue

# 或完成 merge（如果使用 merge）
git commit
```

### 4. 同步其他分支

如果您有其他分支也需要同步：

```bash
# 切换到目标分支
git checkout <branch-name>

# 获取上游更新
git fetch upstream

# 变基或合并
git rebase upstream/main
# 或
git merge upstream/main

# 推送到您的 fork
git push origin <branch-name>
```

## 最佳实践

### 1. 定期同步

建议每周或在上游有重要更新时进行同步，避免积累过多差异。

### 2. 在独立分支上开发

```bash
# 创建功能分支
git checkout -b feature/your-feature

# 在该分支上进行开发和提交
# ...

# 完成后合并回 main
git checkout main
git merge feature/your-feature
```

这样可以减少同步时的冲突。

### 3. 同步前备份

在进行大规模同步前，可以创建备份分支：

```bash
git branch backup-before-sync
```

### 4. 检查差异

同步前可以先查看上游有哪些更新：

```bash
git fetch upstream
git log HEAD..upstream/main --oneline
```

## 常见问题

### Q: 如何移除上游远程仓库？

```bash
git remote remove upstream
```

### Q: 如何更改上游远程仓库的 URL？

```bash
git remote set-url upstream <new-url>
```

### Q: push 时被拒绝怎么办？

如果使用 rebase 后推送被拒绝，使用：

```bash
git push --force-with-lease origin main
```

**注意**：`--force-with-lease` 比 `--force` 更安全，它会检查是否有其他人的提交。

### Q: 如何只同步特定文件？

```bash
# 从上游检出特定文件
git checkout upstream/main -- path/to/file
```

### Q: 如何查看我的 fork 和上游的差异？

```bash
git fetch upstream
git diff main..upstream/main
```

## 自动化脚本（可选）

您可以创建一个脚本来简化同步过程：

**sync_upstream.sh (Linux/Mac)**

```bash
#!/bin/bash
echo "开始同步上游更新..."

# 保存当前分支
CURRENT_BRANCH=$(git branch --show-current)

# 切换到 main
git checkout main

# 获取上游更新
git fetch upstream

# 显示将要更新的提交
echo "即将更新的提交："
git log HEAD..upstream/main --oneline

# 确认是否继续
read -p "是否继续同步？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    # 变基
    git rebase upstream/main

    # 推送
    git push --force-with-lease origin main

    echo "同步完成！"
else
    echo "已取消同步"
fi

# 恢复原分支
git checkout $CURRENT_BRANCH
```

**sync_upstream.ps1 (Windows PowerShell)**

```powershell
Write-Host "开始同步上游更新..." -ForegroundColor Green

# 保存当前分支
$CURRENT_BRANCH = git branch --show-current

# 切换到 main
git checkout main

# 获取上游更新
git fetch upstream

# 显示将要更新的提交
Write-Host "即将更新的提交：" -ForegroundColor Yellow
git log HEAD..upstream/main --oneline

# 确认是否继续
$confirm = Read-Host "是否继续同步？(y/n)"
if ($confirm -eq 'y' -or $confirm -eq 'Y') {
    # 变基
    git rebase upstream/main

    # 推送
    git push --force-with-lease origin main

    Write-Host "同步完成！" -ForegroundColor Green
} else {
    Write-Host "已取消同步" -ForegroundColor Red
}

# 恢复原分支
git checkout $CURRENT_BRANCH
```

## 注意事项

1. **中文文档不会自动同步**：您翻译的 README.md、SECURITY.md 等中文文档是您自己的修改，同步时可能会被覆盖。建议：

   - 将这些文件放在单独的分支管理
   - 或在同步后重新应用您的翻译
   - 或使用 `.gitattributes` 标记这些文件为本地保留

2. **保留自定义修改**：如果您对源代码进行了修改，同步时要特别注意冲突解决。

3. **测试同步后的代码**：同步后务必运行测试确保功能正常：

   ```bash
   cd packages/markitdown
   hatch test
   ```

4. **查看官方更新日志**：同步前查看上游的 Release Notes，了解重大变更。

## 相关资源

- [GitHub Docs: Syncing a fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork)
- [Git Rebase 文档](https://git-scm.com/docs/git-rebase)
- [Git Merge 文档](https://git-scm.com/docs/git-merge)
