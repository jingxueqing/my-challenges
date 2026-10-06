# 违规标签测试

段落包含脚本：<script>alert("xss")</script> 和样式块 <style>p{color:red}</style>。

还有 iframe：<iframe src="https://example.com"></iframe> 与 svg <svg><circle r="10"/></svg>。

视频标签 <video src="a.mp4"></video> 和音频 <audio src="a.mp3"></audio>。

带属性的：<p class="x" id="y" onclick="go()">属性测试</p>

内联样式 position:absolute 的文字。

媒体查询 @media (max-width:100px){body{color:red}}。
