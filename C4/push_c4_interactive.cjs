#!/usr/bin/env node
/**
 * 交互式推送：从终端读入 GitHub PAT（不回显、不进聊天记录），然后执行 C4 推送
 *
 * 用法： node push_c4_interactive.cjs
 */
const { spawnSync } = require('child_process');
const readline = require('readline');

const rl = readline.createInterface({ input: process.stdin, terminal: false });

process.stdout.write(
  '\n=== C4 交付物推送（jingxueqing/my-challenges -> C4/）===\n' +
  '请粘贴 GitHub 个人访问令牌（PAT，需 repo 作用域），然后按回车。\n' +
  '（令牌只用于本次推送，不会被打印或写入任何文件）\n\n' +
  'token> '
);

rl.once('line', (answer) => {
  rl.close();
  const token = (answer || '').trim();
  if (!token) {
    console.error('\n未输入令牌，已退出，未做任何上传。');
    process.exit(2);
  }
  console.log(`\n已收到令牌（长度 ${token.length}）。开始推送 30 个文件 ...\n`);
  const r = spawnSync(process.execPath, ['push_c4_to_github.cjs'], {
    cwd: __dirname,
    env: Object.assign({}, process.env, { GH_TOKEN: token }),
    stdio: 'inherit'
  });
  console.log('\n=== 推送结束，可以关闭此面板 ===');
  process.exit(typeof r.status === 'number' ? r.status : 1);
});
