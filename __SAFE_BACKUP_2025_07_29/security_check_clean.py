#!/usr/bin/env python3
"""
🛡️ HOOK BOOST - SECURITY CHECKER (CLEAN VERSION)
Automatyczne sprawdzenie bezpieczeństwa kodu bez wzorców tokenów
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any

class SecurityChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.issues = []
        self.excluded_dirs = {
            '.git', '.venv', '.venv-1', '__pycache__', 
            'node_modules', '.env', 'venv', 'env'
        }
        
        # Ogólne wzorce niebezpiecznych tokenów (bez konkretnych wartości)
        self.dangerous_patterns = [
            r'[A-Za-z0-9]{24}\.[A-Za-z0-9_.-]{6}\.[A-Za-z0-9_-]{27}',  # Discord token pattern
            r'ghp_[A-Za-z0-9]{36}',                                     # GitHub PAT
            r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',  # UUID/Railway
            r'AIza[A-Za-z0-9_-]{35}',                                   # Google API key pattern
            r'sk-[A-Za-z0-9]{48}',                                      # OpenAI key pattern
        ]
        
        # Słowa kluczowe wskazujące na tokeny
        self.dangerous_keywords = [
            'token', 'api_key', 'secret', 'password', 'credential'
        ]

    def scan_file(self, file_path: Path) -> List[Dict]:
        """Skanuje pojedynczy plik pod kątem niebezpiecznych wzorców"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Sprawdź wzorce tokenów
            for pattern in self.dangerous_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    issues.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': line_number,
                        'type': 'TOKEN_PATTERN',
                        'pattern': 'SUSPECTED_TOKEN',
                        'context': 'TOKEN_DETECTED'
                    })
            
            # Sprawdź hardcodowane przypisania
            hardcoded_patterns = [
                r'TOKEN\s*=\s*["\'][^"\']{20,}["\']',
                r'API_KEY\s*=\s*["\'][^"\']{20,}["\']',
                r'SECRET\s*=\s*["\'][^"\']{20,}["\']',
            ]
            
            for pattern in hardcoded_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    issues.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': line_number,
                        'type': 'HARDCODED_TOKEN',
                        'severity': 'CRITICAL'
                    })
                    
        except Exception as e:
            pass  # Ignoruj pliki których nie można przeczytać
            
        return issues

    def scan_directory(self) -> List[Dict]:
        """Skanuje cały projekt"""
        all_issues = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Pomiń excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            
            for file in files:
                file_path = Path(root) / file
                
                # Skanuj tylko pliki tekstowe
                if file_path.suffix in {'.py', '.sh', '.txt', '.json', '.env', '.md', '.yml', '.yaml'}:
                    issues = self.scan_file(file_path)
                    all_issues.extend(issues)
                    
        return all_issues

    def check_gitignore(self) -> List[Dict]:
        """Sprawdza czy .gitignore prawidłowo chroni wrażliwe pliki"""
        issues = []
        gitignore_path = self.project_root / '.gitignore'
        
        if not gitignore_path.exists():
            issues.append({
                'type': 'MISSING_GITIGNORE',
                'severity': 'HIGH',
                'message': 'Brak głównego pliku .gitignore'
            })
            return issues
            
        try:
            with open(gitignore_path, 'r') as f:
                gitignore_content = f.read()
                
            # Sprawdź czy chroni ważne wzorce
            important_patterns = ['.env', '*.log', '__pycache__', 'secrets.json']
            for pattern in important_patterns:
                if pattern not in gitignore_content:
                    issues.append({
                        'type': 'GITIGNORE_MISSING_PATTERN',
                        'severity': 'MEDIUM',
                        'pattern': pattern,
                        'message': f'Wzorzec "{pattern}" nie jest w .gitignore'
                    })
                    
        except Exception as e:
            issues.append({
                'type': 'GITIGNORE_READ_ERROR',
                'severity': 'MEDIUM',
                'error': str(e)
            })
            
        return issues

    def check_env_files(self) -> List[Dict]:
        """Sprawdza konfigurację plików środowiskowych"""
        issues = []
        
        # Sprawdź czy .env istnieje
        env_path = self.project_root / '.env'
        env_template_path = self.project_root / 'env.template'
        
        if env_path.exists():
            issues.append({
                'type': 'ENV_FILE_EXISTS',
                'severity': 'WARNING',
                'message': 'Plik .env istnieje - upewnij się że jest w .gitignore'
            })
            
        if not env_template_path.exists():
            issues.append({
                'type': 'MISSING_ENV_TEMPLATE',
                'severity': 'LOW',
                'message': 'Brak pliku env.template'
            })
            
        return issues

    def generate_report(self) -> Dict[str, Any]:
        """Generuje pełny raport bezpieczeństwa"""
        print("🔍 Skanowanie bezpieczeństwa HOOK BOOST...")
        
        # Zbierz wszystkie problemy
        token_issues = self.scan_directory()
        gitignore_issues = self.check_gitignore()
        env_issues = self.check_env_files()
        
        # Policz severity
        critical_count = len([i for i in token_issues if i.get('severity') == 'CRITICAL'])
        high_count = len([i for i in token_issues + gitignore_issues + env_issues if i.get('severity') == 'HIGH'])
        
        report = {
            'timestamp': os.popen('date').read().strip(),
            'total_issues': len(token_issues) + len(gitignore_issues) + len(env_issues),
            'critical_issues': critical_count,
            'high_issues': high_count,
            'token_issues': token_issues,
            'gitignore_issues': gitignore_issues,
            'env_issues': env_issues,
            'security_score': self._calculate_security_score(critical_count, high_count)
        }
        
        return report

    def _calculate_security_score(self, critical: int, high: int) -> str:
        """Oblicza ogólny poziom bezpieczeństwa"""
        if critical > 0:
            return "🚨 KRYTYCZNY - Natychmiastowe działanie wymagane!"
        elif high > 0:
            return "⚠️  WYSOKI - Wymaga szybkiej naprawy"
        else:
            return "✅ DOBRY - Podstawowe zabezpieczenia w porządku"

    def print_report(self, report: Dict[str, Any]):
        """Wyświetla raport w konsoli"""
        print("\n" + "="*70)
        print("🛡️  RAPORT BEZPIECZEŃSTWA HOOK BOOST")
        print("="*70)
        
        print(f"📅 Data skanowania: {report['timestamp']}")
        print(f"🔢 Znalezione problemy: {report['total_issues']}")
        print(f"🎯 Wynik bezpieczeństwa: {report['security_score']}")
        print()
        
        # Krytyczne problemy
        if report['critical_issues'] > 0:
            print("🚨 KRYTYCZNE PROBLEMY:")
            for issue in report['token_issues']:
                if issue.get('severity') == 'CRITICAL':
                    print(f"   ❌ {issue['file']}:{issue['line']} - Wykryty hardcodowany token!")
            print()
        
        # Problemy z tokenami
        if report['token_issues']:
            print("🔑 WYKRYTE WZORCE TOKENÓW:")
            for issue in report['token_issues']:
                if issue['type'] == 'TOKEN_PATTERN':
                    print(f"   ⚠️  {issue['file']}:{issue['line']} - Podejrzany wzorzec")
            print()
        
        # Problemy z .gitignore
        if report['gitignore_issues']:
            print("📁 PROBLEMY .GITIGNORE:")
            for issue in report['gitignore_issues']:
                print(f"   📝 {issue.get('message', 'Problem z .gitignore')}")
            print()
        
        # Rekomendacje
        print("💡 ZALECENIA:")
        if report['critical_issues'] > 0:
            print("   1. 🚨 NATYCHMIAST usuń hardcodowane tokeny!")
            print("   2. 🔄 Utwórz nowe tokeny w dashboardach serwisów")
            print("   3. 📝 Przenieś tokeny do plików .env")
        
        if report['total_issues'] > 0:
            print("   4. 🛡️  Przeczytaj SECURITY_SETUP_CLEAN.md")
            print("   5. ✅ Uruchom ponownie po naprawach")
        else:
            print("   ✅ Podstawowe zabezpieczenia wyglądają dobrze!")
        
        print("\n" + "="*70)

def main():
    """Główna funkcja"""
    checker = SecurityChecker()
    report = checker.generate_report()
    checker.print_report(report)
    
    # Zapisz raport do pliku (bez szczegółów tokenów)
    safe_report = {
        'timestamp': report['timestamp'],
        'total_issues': report['total_issues'],
        'critical_issues': report['critical_issues'],
        'high_issues': report['high_issues'],
        'security_score': report['security_score'],
        'summary': 'Raport bezpieczeństwa bez wrażliwych danych'
    }
    
    with open('security_report_clean.json', 'w') as f:
        json.dump(safe_report, f, indent=2)
    
    print(f"📄 Bezpieczny raport zapisany w: security_report_clean.json")
    
    # Exit code dla CI/CD
    if report['critical_issues'] > 0:
        exit(1)  # Fail jeśli krytyczne problemy
    elif report['total_issues'] > 0:
        exit(2)  # Warning jeśli inne problemy
    else:
        exit(0)  # Success

if __name__ == "__main__":
    main() 