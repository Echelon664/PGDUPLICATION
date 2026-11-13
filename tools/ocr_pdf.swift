// Print the text of a scanned PDF using macOS Vision OCR, one line per page.
// Usage: swift tools/ocr_pdf.swift path/to/file.pdf
// macOS only. Each page is read in all four orientations and the one that
// yields the most text wins, since some County scans are rotated.
import Foundation
import PDFKit
import Vision
import AppKit

let url = URL(fileURLWithPath: CommandLine.arguments[1])
guard let doc = PDFDocument(url: url) else {
    FileHandle.standardError.write("Cannot open \(url.path)\n".data(using: .utf8)!)
    exit(1)
}
for i in 0..<doc.pageCount {
    guard let page = doc.page(at: i) else { continue }
    // thumbnail() applies the page's /Rotate, so rotated scans are not clipped.
    let box = page.bounds(for: .mediaBox)
    let rotated = page.rotation % 180 != 0
    let size = CGSize(width: (rotated ? box.height : box.width) * 3, height: (rotated ? box.width : box.height) * 3)
    let thumb = page.thumbnail(of: size, for: .mediaBox)
    guard let image = thumb.cgImage(forProposedRect: nil, context: nil, hints: nil) else { continue }
    var best: [String] = []
    for orientation in [CGImagePropertyOrientation.up, .left, .right, .down] {
        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        try? VNImageRequestHandler(cgImage: image, orientation: orientation).perform([request])
        let lines = (request.results ?? []).compactMap { $0.topCandidates(1).first?.string }
        if lines.joined().count > best.joined().count { best = lines }
    }
    print(best.joined(separator: " "))
}
