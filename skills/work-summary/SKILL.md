---
name: work-summary
allowed-tools: Read, Bash(git log *), Bash(git config *), Grep, Glob
description: generative work summary report
disable-model-invocation: false
---

# Generate a comprehensive report for the given period of time

根据给定的时间段，基于 git commit 日志生成一份综合工作任务报告。

1. 用列表输出工作项
2. 每项不超过20字符
3. 默认时间段为最近7天
