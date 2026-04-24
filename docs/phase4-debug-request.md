# Flutter 디버그 요청: 다이얼로그 닫기 후 새 UI가 표시되지 않는 문제

## 문제 요약

Flutter 앱에서 `showDialog` → 사용자가 버튼 클릭 → `Navigator.pop(context)` 으로 다이얼로그 닫기 → 이후 **어떤 UI도 표시되지 않음** (AlertDialog, BottomSheet, SnackBar 모두 안 됨).

## 환경
- Flutter 3.27+ / Dart 3.6+
- Android 16 (API 36), Samsung SM-A155N
- 상태관리: StatefulWidget + setState (Provider 있지만 이 화면에선 미사용)

## 앱 구조

```
MaterialApp
  └─ MainScreen (Scaffold + BottomNavigationBar 6탭)
      └─ IndexedStack
          ├─ HomeScreen
          ├─ ...
          └─ MonitoringScreen (★ 문제 화면)
              └─ Scaffold (자체 Scaffold 있음 — 이중 Scaffold 구조)
                  └─ TabBarView (3탭)
                      └─ 시민 제보 탭
```

**핵심: MainScreen에 Scaffold가 있고, MonitoringScreen에도 자체 Scaffold가 있음 (이중 Scaffold)**

## 현재 코드 흐름

### 1단계: 제보 다이얼로그 표시
```dart
// _MonitoringScreenState 클래스 내부 메서드
void _showReportDialogFor(Map<String, dynamic>? lm) async {
    final prefs = await SharedPreferences.getInstance();
    final userName = (prefs.getString('memberName') ?? '익명 시민').trim();

    if (!mounted) return;
    showDialog(
      context: context,  // _MonitoringScreenState.context
      builder: (context) => StatefulBuilder(  // 여기서 context가 다이얼로그 context로 shadow됨
        builder: (context, setDialogState) => AlertDialog(
          // ... 입력 필드들 ...
          actions: [
            ElevatedButton(
              onPressed: () async {
                // 입력값 저장
                final savedTitle = titleC.text;
                // ...

                // 다이얼로그 닫기
                Navigator.pop(context);  // ← 이 context는 다이얼로그의 context

                // API 호출 + 결과 표시
                _submitAndShowResult(  // ← 이것이 호출되는지, 안 되는지가 핵심
                  district: savedDistrict,
                  // ...
                );
              },
            ),
          ],
        ),
      ),
    );
}
```

### 2단계: API 호출 + 결과 표시 (이 메서드가 동작하지 않음)
```dart
Future<void> _submitAndShowResult({
    required String district,
    required String monaCd,
    required String reportType,
    required String title,
    required String content,
    String? newsUrl,
    required String userName,
}) async {
    await Future.delayed(const Duration(milliseconds: 500));
    if (!mounted) return;  // ← 여기서 return 되는 것인지?

    try {
      final result = await ApiService.submitDistrictReport(
        district: district,
        monaCd: monaCd,
        reportType: reportType,
        title: title,
        content: content,
        newsUrl: newsUrl,
        userName: userName,
      );

      if (!mounted) return;  // ← 여기서 return 되는 것인지?
      final reportId = result['report']?['id'];

      // 이 showDialog가 절대 표시되지 않음
      showDialog(
        context: this.context,  // _MonitoringScreenState.context
        builder: (ctx) => AlertDialog(
          title: const Text('디버그: 제보 결과'),
          content: Text('reportId=$reportId'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('닫기'),
            ),
          ],
        ),
      );
    } catch (e) {
      if (!mounted) return;
      // 이 showDialog도 절대 표시되지 않음
      showDialog(
        context: this.context,
        builder: (ctx) => AlertDialog(
          title: const Text('디버그: 오류'),
          content: Text('$e'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('확인'),
            ),
          ],
        ),
      );
    }
}
```

## 확인된 사실

1. **서버에는 제보가 등록됨** — API 호출 후 DB에 새 레코드 확인됨 (4건 → 7건 증가)
2. **다이얼로그는 정상적으로 닫힘** — Navigator.pop 동작 확인
3. **SnackBar도 안 됨** — 이전에 SnackBar 방식도 시도했으나 표시 안 됨
4. **showModalBottomSheet도 안 됨** — BottomSheet도 시도했으나 표시 안 됨
5. **showDialog도 안 됨** — 가장 간단한 AlertDialog도 표시 안 됨
6. **에러 다이얼로그도 안 보임** — catch 블록의 AlertDialog도 표시되지 않음
7. **빌드 에러 없음** — dart analyze 통과, APK 정상 빌드

## 시도한 방법들 (전부 실패)

### 시도 1: SnackBar
```dart
Navigator.pop(context);
ScaffoldMessenger.of(this.context).showSnackBar(SnackBar(...));
// 결과: 안 보임
```

### 시도 2: 즉시 BottomSheet
```dart
Navigator.pop(context);
if (!mounted) return;
_showOntologyResultSheet(reportId, title);  // showModalBottomSheet 호출
// 결과: 안 보임
```

### 시도 3: 별도 메서드 + 500ms 지연 + AlertDialog
```dart
Navigator.pop(context);
_submitAndShowResult(...);  // 내부에서 500ms 대기 후 showDialog
// 결과: 안 보임
```

## 의심되는 원인 (확인 필요)

1. **`mounted` 가 false**: IndexedStack 안의 Scaffold에서 다이얼로그를 닫은 후 State가 unmounted 상태가 되는가?
2. **이중 Scaffold 문제**: MainScreen.Scaffold > MonitoringScreen.Scaffold 구조에서 context 해석 문제?
3. **`_submitAndShowResult`가 호출되지 않음**: Navigator.pop 후 onPressed async 함수가 중단되는가?
4. **StatefulBuilder의 context shadowing**: builder 파라미터 `context`가 외부 `context`를 가리는 문제?
5. **`submitDistrictReport` 가 응답을 영영 기다림**: timeout 10초인데 실제로 hang 상태?

## ApiService.submitDistrictReport 코드
```dart
static Future<Map<String, dynamic>> submitDistrictReport({
    required String district,
    required String monaCd,
    required String reportType,
    required String title,
    required String content,
    String? newsUrl,
    List<String>? photoUrls,
    String? userName,
}) async {
    final r = await http
        .post(
          Uri.parse('$baseUrl/api/districts/report'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'district': district,
            'mona_cd': monaCd,
            'report_type': reportType,
            'title': title,
            'content': content,
            'news_url': newsUrl,
            'photo_urls': photoUrls ?? [],
            'user_name': userName ?? '익명 시민',
          }),
        )
        .timeout(const Duration(seconds: 10));  // _timeout = 10초
    return jsonDecode(r.body);
    // try-catch 없음!
}
```

## 요청사항

1. 위 코드에서 **다이얼로그 닫기 후 새 UI가 표시되지 않는 근본 원인**은 무엇인가?
2. **이중 Scaffold + IndexedStack** 구조에서 이 문제를 해결하는 정확한 방법은?
3. 가능하면 **수정된 코드**를 제공해주세요.

핵심 제약사항:
- MonitoringScreen의 자체 Scaffold 제거 불가 (TabBar가 AppBar에 들어있음)
- MainScreen의 IndexedStack 구조 변경 불가 (6탭 구조 유지)
- 제보 등록 성공 후 AI 분석 결과를 사용자에게 보여주는 것이 최종 목표
