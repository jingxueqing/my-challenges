// C1 管线组件：PDF -> 文本（macOS 原生 Vision OCR，无网络、无第三方依赖）
// 用法：ocr <input.pdf> <output.txt>
// 适用：图片型 PDF / 无字体表 PDF（常规 FlateDecode 抽取拿不到文字的讲义）

import Foundation
import PDFKit
import Vision
import AppKit

let args = CommandLine.arguments
guard args.count >= 3 else {
    FileHandle.standardError.write("usage: ocr <input.pdf> <output.txt>\n".data(using: .utf8)!)
    exit(1)
}
let pdfPath = args[1]
let outPath = args[2]

guard let doc = PDFDocument(url: URL(fileURLWithPath: pdfPath)) else {
    FileHandle.standardError.write("cannot open pdf: \(pdfPath)\n".data(using: .utf8)!)
    exit(2)
}

let scale: CGFloat = 2.0
var blocks: [String] = []
var skipped: [Int] = []

for i in 0..<doc.pageCount {
    guard let page = doc.page(at: i) else { continue }
    let bounds = page.bounds(for: .mediaBox)
    let w = Int(bounds.width * scale), h = Int(bounds.height * scale)
    guard w > 0, h > 0,
          let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8,
                              bytesPerRow: 0, space: CGColorSpaceCreateDeviceRGB(),
                              bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue) else { continue }
    ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
    ctx.scaleBy(x: scale, y: scale)
    page.draw(with: .mediaBox, to: ctx)
    guard let img = ctx.makeImage() else { continue }

    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = true
    req.recognitionLanguages = ["en-US"]

    do {
        try VNImageRequestHandler(cgImage: img, options: [:]).perform([req])
    } catch {
        skipped.append(i + 1)
        continue
    }

    let obs = (req.results ?? []).compactMap { $0 as? VNRecognizedTextObservation }
    let lines = obs.sorted { a, b in
        if abs(a.boundingBox.midY - b.boundingBox.midY) > 0.01 { return a.boundingBox.midY > b.boundingBox.midY }
        return a.boundingBox.minX < b.boundingBox.minX
    }.compactMap { $0.topCandidates(1).first?.string }

    let text = lines.joined(separator: "\n").trimmingCharacters(in: .whitespacesAndNewlines)
    if text.isEmpty {
        skipped.append(i + 1)
    } else {
        blocks.append("## Page \(i + 1)\n\n" + text)
    }
    FileHandle.standardError.write("  page \(i + 1)/\(doc.pageCount) -> \(text.count) chars\n".data(using: .utf8)!)
}

let body = blocks.joined(separator: "\n\n")
try? body.write(toFile: outPath, atomically: true, encoding: .utf8)
let name = (pdfPath as NSString).lastPathComponent
let skipStr = skipped.map(String.init).joined(separator: ",")
print("{\"pdf\":\"\(name)\",\"pages\":\(doc.pageCount),\"chars\":\(body.count),\"skipped\":\"\(skipStr)\"}")
