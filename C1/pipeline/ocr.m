// C1 管线组件：PDF -> 文本（macOS 原生 Vision OCR，无网络、无第三方依赖）
// 用法：ocr <input.pdf> <output.txt>
// 适用：图片型 PDF / 无字体表 PDF（常规 FlateDecode 抽取拿不到文字的讲义）
// 说明：本机 Command Line Tools 的 Swift 工具链版本不匹配，故用 ObjC + clang 调用同一套系统框架。

#import <Foundation/Foundation.h>
#import <PDFKit/PDFKit.h>
#import <Vision/Vision.h>
#import <AppKit/AppKit.h>

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        if (argc < 3) { fprintf(stderr, "usage: ocr <input.pdf> <output.txt>\n"); return 1; }
        NSString *inPath = [NSString stringWithUTF8String:argv[1]];
        NSString *outPath = [NSString stringWithUTF8String:argv[2]];

        PDFDocument *doc = [[PDFDocument alloc] initWithURL:[NSURL fileURLWithPath:inPath]];
        if (!doc) { fprintf(stderr, "cannot open pdf: %s\n", argv[1]); return 2; }

        NSMutableArray *blocks = [NSMutableArray array];
        NSMutableArray *skipped = [NSMutableArray array];
        CGFloat scale = 2.0;
        NSUInteger n = [doc pageCount];

        for (NSUInteger i = 0; i < n; i++) {
            PDFPage *page = [doc pageAtIndex:i];
            if (!page) continue;
            NSRect b = [page boundsForBox:kPDFDisplayBoxMediaBox];
            size_t w = (size_t)(b.size.width * scale), h = (size_t)(b.size.height * scale);
            if (w == 0 || h == 0) continue;

            CGColorSpaceRef cs = CGColorSpaceCreateDeviceRGB();
            CGContextRef ctx = CGBitmapContextCreate(NULL, w, h, 8, 0, cs,
                                                     (CGBitmapInfo)kCGImageAlphaPremultipliedFirst);
            CGColorSpaceRelease(cs);
            if (!ctx) continue;
            CGContextSetRGBFillColor(ctx, 1, 1, 1, 1);
            CGContextFillRect(ctx, CGRectMake(0, 0, w, h));
            CGContextScaleCTM(ctx, scale, scale);
            [page drawWithBox:kPDFDisplayBoxMediaBox toContext:ctx];
            CGImageRef img = CGBitmapContextCreateImage(ctx);
            CGContextRelease(ctx);
            if (!img) continue;

            VNRecognizeTextRequest *req = [[VNRecognizeTextRequest alloc] init];
            req.recognitionLevel = VNRequestTextRecognitionLevelAccurate;
            req.usesLanguageCorrection = YES;
            req.recognitionLanguages = @[@"zh-Hans", @"en-US", @"zh-Hant"];

            VNImageRequestHandler *handler = [[VNImageRequestHandler alloc] initWithCGImage:img options:@{}];
            NSError *err = nil;
            BOOL ok = [handler performRequests:@[req] error:&err];
            CGImageRelease(img);
            if (!ok) { [skipped addObject:@(i + 1)]; continue; }

            NSArray *sorted = [req.results sortedArrayUsingComparator:^NSComparisonResult(VNRecognizedTextObservation *a, VNRecognizedTextObservation *b) {
                CGRect ra = a.boundingBox, rb = b.boundingBox;
                if (fabs(CGRectGetMidY(ra) - CGRectGetMidY(rb)) > 0.01) {
                    return CGRectGetMidY(ra) > CGRectGetMidY(rb) ? NSOrderedAscending : NSOrderedDescending;
                }
                return CGRectGetMinX(ra) < CGRectGetMinX(rb) ? NSOrderedAscending : NSOrderedDescending;
            }];

            NSMutableArray *lines = [NSMutableArray array];
            for (VNRecognizedTextObservation *o in sorted) {
                VNRecognizedText *t = [[o topCandidates:1] firstObject];
                if (t.string.length) [lines addObject:t.string];
            }
            NSString *text = [[lines componentsJoinedByString:@"\n"]
                              stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]];
            if (text.length == 0) {
                [skipped addObject:@(i + 1)];
            } else {
                [blocks addObject:[NSString stringWithFormat:@"## Page %lu\n\n%@", (unsigned long)(i + 1), text]];
            }
            fprintf(stderr, "  page %lu/%lu -> %lu chars\n",
                    (unsigned long)(i + 1), (unsigned long)n, (unsigned long)text.length);
        }

        NSString *body = [blocks componentsJoinedByString:@"\n\n"];
        [body writeToFile:outPath atomically:YES encoding:NSUTF8StringEncoding error:NULL];

        NSMutableArray *sk = [NSMutableArray array];
        for (NSNumber *x in skipped) [sk addObject:[x stringValue]];
        printf("{\"pdf\":\"%s\",\"pages\":%lu,\"chars\":%lu,\"skipped\":\"%s\"}\n",
               [[inPath lastPathComponent] UTF8String], (unsigned long)n,
               (unsigned long)body.length,
               [[sk componentsJoinedByString:@","] UTF8String]);
    }
    return 0;
}
