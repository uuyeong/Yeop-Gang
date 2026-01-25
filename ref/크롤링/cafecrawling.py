import time
from selenium import webdriver
import csv
import pandas as pd
from bs4 import BeautifulSoup as bs
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchFrameException, UnexpectedAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
import re
import random
import time

url='https://nid.naver.com/nidlogin.login'
id='dohommd'
pw='3x3x3xce$'

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# 고급 스크랩 방지 우회 설정
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--remote-debugging-port=9222")

# 실제 브라우저처럼 보이게 하는 User-Agent
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# chrome_options.add_argument("headless") # headless option
browser = webdriver.Chrome(options=chrome_options)

# 자동화 감지 우회
browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
browser.execute_cdp_cmd('Network.setUserAgentOverride', {
    "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})
browser.get(url)

browser.implicitly_wait(2)

browser.execute_script(f"document.getElementsByName('id')[0].value=\'{id}\'")
browser.execute_script(f"document.getElementsByName('pw')[0].value=\'{pw}\'")

browser.find_element(by=By.XPATH,value='//*[@id="log.login"]').click()
time.sleep(0.5)

baseurl = 'https://cafe.naver.com'

def random_delay(min_seconds=0.1, max_seconds=0.5):
    """빠른 랜덤 지연으로 최소한의 자연스러운 행동 모방"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def human_like_scroll(browser):
    """빠른 스크롤로 페이지 활성화"""
    actions = ActionChains(browser)
    actions.scroll_by_amount(0, 200).perform()
    random_delay(0.1, 0.3)

def wait_for_page_load(browser, timeout=5):
    """빠른 페이지 로딩 대기"""
    try:
        WebDriverWait(browser, timeout).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        random_delay(0.2, 0.5)
    except:
        random_delay(0.5, 1.0)

def format_comments_for_csv(comments):
    """댓글 데이터를 CSV 저장용 문자열로 변환"""
    if not comments:
        return "댓글없음"
    
    formatted_comments = []
    for comment in comments:
        # 댓글 정보를 하나의 문자열로 결합
        comment_str = f"[작성자:{comment['author']}|내용:{comment['content']}|날짜:{comment['date']}]"
        formatted_comments.append(comment_str)
    
    # 모든 댓글을 구분자로 연결
    return " || ".join(formatted_comments)

def debug_page_structure_for_comments(article_soup):
    """댓글 구조를 디버깅하는 함수"""
    print("=== 댓글 구조 디버깅 ===")
    
    # 모든 클래스가 'comment'를 포함하는 요소 찾기
    comment_elements = article_soup.find_all(class_=lambda x: x and 'comment' in x.lower())
    print(f"'comment' 포함 클래스 요소: {len(comment_elements)}개")
    for i, elem in enumerate(comment_elements[:5]):  # 처음 5개만 출력
        print(f"  [{i}] {elem.name} - 클래스: {elem.get('class', [])}")
    
    # 모든 클래스가 'reply'를 포함하는 요소 찾기
    reply_elements = article_soup.find_all(class_=lambda x: x and 'reply' in x.lower())
    print(f"'reply' 포함 클래스 요소: {len(reply_elements)}개")
    for i, elem in enumerate(reply_elements[:5]):
        print(f"  [{i}] {elem.name} - 클래스: {elem.get('class', [])}")
    
    # 모든 li 요소 찾기
    li_elements = article_soup.find_all('li')
    print(f"전체 li 요소: {len(li_elements)}개")
    for i, elem in enumerate(li_elements[:10]):  # 처음 10개만 출력
        classes = elem.get('class', [])
        if classes:
            print(f"  [{i}] li - 클래스: {classes}")
    
    # 모든 div 요소 중 댓글 관련 찾기
    div_elements = article_soup.find_all('div')
    comment_divs = [div for div in div_elements if div.get('class') and any('comment' in str(cls).lower() for cls in div.get('class', []))]
    print(f"댓글 관련 div 요소: {len(comment_divs)}개")
    for i, elem in enumerate(comment_divs[:5]):
        print(f"  [{i}] div - 클래스: {elem.get('class', [])}")
    
    print("=== 디버깅 완료 ===\n")

def crawl_comments(article_soup, article_href):
    """댓글을 크롤링하는 함수"""
    comments = []
    
    # 먼저 페이지 구조 디버깅
    debug_page_structure_for_comments(article_soup)
    
    try:
        # 네이버 카페 실제 댓글 선택자들
        comment_selectors = [
            '.CommentItem',
            '.comment_area', 
            '.comment_box',
            '.comment_text_box',
            '.text_comment',
            '.comment-list',
            '.reply-list',
            '.comment-area',
            '.reply-area',
            '[class*="CommentItem"]',
            '[class*="comment"]',
            '[class*="reply"]',
            '[id*="comment"]',
            '[id*="reply"]'
        ]
        
        comment_area = None
        for selector in comment_selectors:
            comment_area = article_soup.select_one(selector)
            if comment_area:
                print(f"댓글 영역 발견: {selector}")
                break
        
        if not comment_area:
            print("댓글 영역을 찾을 수 없습니다. 다른 방법으로 시도합니다.")
            
            # 모든 li 요소에서 댓글 찾기
            all_li = article_soup.find_all('li')
            print(f"전체 li 요소 {len(all_li)}개를 검사합니다.")
            
            for li in all_li:
                li_text = li.get_text().strip()
                if len(li_text) > 10 and len(li_text) < 500:  # 댓글 길이 범위
                    # 댓글 같은 패턴 찾기
                    if any(keyword in li_text for keyword in ['님', '님께서', '작성', '댓글']):
                        print(f"잠재적 댓글 발견: {li_text[:50]}...")
                        comments.append({
                            'author': 'unknown',
                            'content': li_text,
                            'date': 'unknown',
                            'article_url': article_href
                        })
            
            if comments:
                print(f"대체 방법으로 댓글 {len(comments)}개 발견")
                return comments
            else:
                print("댓글을 찾을 수 없습니다.")
                return comments
        
        # 댓글 항목들 찾기 - 더 포괄적인 방법
        comment_items = []
        
        # 방법 1: 특정 클래스로 찾기
        for keyword in ['CommentItem', 'comment_area', 'comment_box', 'comment_text_box', 'text_comment', 'comment', 'reply']:
            items = comment_area.find_all(['li', 'div'], class_=lambda x: x and keyword.lower() in str(x).lower())
            if items:
                comment_items.extend(items)
                print(f"'{keyword}' 클래스로 {len(items)}개 항목 발견")
        
        # 방법 2: 모든 li와 div 요소 찾기
        if not comment_items:
            comment_items = comment_area.find_all(['li', 'div'])
            print(f"전체 li/div 요소 {len(comment_items)}개 발견")
        
        # 방법 3: 텍스트 내용으로 댓글 필터링
        if comment_items:
            filtered_items = []
            for item in comment_items:
                text = item.get_text().strip()
                if len(text) > 5 and len(text) < 1000:  # 댓글 길이 범위
                    # 댓글 같은 패턴 확인
                    if any(pattern in text for pattern in ['님', '님께서', '작성', '댓글', '답글', '좋아요']):
                        filtered_items.append(item)
            
            if filtered_items:
                comment_items = filtered_items
                print(f"텍스트 패턴으로 필터링된 댓글 {len(comment_items)}개")
        
        print(f"최종 댓글 항목 {len(comment_items)}개 발견")
        
        for i, comment_item in enumerate(comment_items):
            try:
                # 댓글 작성자
                author_selectors = ['.nick', '.author', '.writer', '.user', '[class*="nick"]']
                comment_author = None
                for selector in author_selectors:
                    author_elem = comment_item.select_one(selector)
                    if author_elem:
                        comment_author = author_elem.get_text().strip()
                        break
                
                if not comment_author:
                    # 버튼이나 링크에서 작성자 찾기
                    author_elem = comment_item.find(['button', 'a'], class_=lambda x: x and 'nick' in x.lower())
                    if author_elem:
                        comment_author = author_elem.get_text().strip()
                
                # 댓글 내용
                content_selectors = ['.comment-text', '.reply-text', '.content', '.text', '[class*="text"]']
                comment_content = None
                for selector in content_selectors:
                    content_elem = comment_item.select_one(selector)
                    if content_elem:
                        comment_content = content_elem.get_text().strip()
                        break
                
                if not comment_content:
                    # 전체 텍스트에서 작성자 제외하고 내용 추출
                    full_text = comment_item.get_text().strip()
                    if comment_author and comment_author in full_text:
                        comment_content = full_text.replace(comment_author, '').strip()
                    else:
                        comment_content = full_text
                
                # 댓글 날짜
                date_selectors = ['.date', '.time', '.regdate', '[class*="date"]']
                comment_date = None
                for selector in date_selectors:
                    date_elem = comment_item.select_one(selector)
                    if date_elem:
                        comment_date = date_elem.get_text().strip()
                        break
                
                # 댓글 데이터가 있으면 추가
                if comment_content and len(comment_content) > 0:
                    comments.append({
                        'author': comment_author or 'unknown',
                        'content': comment_content,
                        'date': comment_date or 'unknown',
                        'article_url': article_href
                    })
                    
            except Exception as e:
                print(f"댓글 {i+1} 처리 중 오류: {e}")
                continue
                
    except Exception as e:
        print(f"댓글 크롤링 중 오류: {e}")
    
    return comments

def is_within_date_range(data, min_year=2024, max_year=2025):
    """게시글이 지정된 연도 범위 내인지 확인하는 함수"""
    try:
        # 이미지에서 확인한 정확한 날짜 클래스 사용
        date_element = data.select_one('td.td_normal.type_date')
        
        if not date_element:
            # 대안으로 다른 날짜 선택자들 시도
            date_selectors = [
                '.date',
                '.regdate', 
                '.time',
                '[class*="date"]',
                'td:nth-child(4)',  # 일반적으로 날짜가 4번째 컬럼
                'td:nth-child(5)',  # 또는 5번째 컬럼
                'span'
            ]
            
            for selector in date_selectors:
                date_element = data.select_one(selector)
                if date_element:
                    break
        
        if not date_element:
            # td 요소들에서 날짜 패턴 찾기
            tds = data.find_all('td')
            for td in tds:
                text = td.get_text().strip()
                if re.match(r'\d{4}\.\d{1,2}\.\d{1,2}', text):  # YYYY.MM.DD 패턴
                    date_element = td
                    break
        
        if not date_element:
            print("날짜 정보를 찾을 수 없습니다.")
            return True  # 날짜를 찾을 수 없으면 포함
        
        date_text = date_element.get_text().strip()
        print(f"게시글 날짜: {date_text}")
        
        # 날짜 파싱
        try:
            # YYYY.MM.DD. 형식 파싱 (이미지에서 확인한 형식)
            if re.match(r'\d{4}\.\d{1,2}\.\d{1,2}\.', date_text):
                # 마지막 점 제거 후 파싱
                clean_date = date_text.rstrip('.')
                date_obj = datetime.strptime(clean_date, '%Y.%m.%d')
                year = date_obj.year
                
                if min_year <= year <= max_year:
                    print(f"✅ {year}년 게시글 포함 ({min_year}~{max_year}년 범위)")
                    return True
                else:
                    print(f"❌ {year}년 게시글 제외 ({min_year}~{max_year}년 범위 외)")
                    return False
            
            # YYYY.MM.DD 형식 파싱 (점 없는 경우)
            elif re.match(r'\d{4}\.\d{1,2}\.\d{1,2}', date_text):
                date_obj = datetime.strptime(date_text, '%Y.%m.%d')
                year = date_obj.year
                
                if min_year <= year <= max_year:
                    print(f"✅ {year}년 게시글 포함 ({min_year}~{max_year}년 범위)")
                    return True
                else:
                    print(f"❌ {year}년 게시글 제외 ({min_year}~{max_year}년 범위 외)")
                    return False
            
            # MM.DD 형식 (올해로 가정)
            elif re.match(r'\d{1,2}\.\d{1,2}', date_text):
                current_year = datetime.now().year
                if min_year <= current_year <= max_year:
                    print(f"✅ 올해 게시글 포함 (MM.DD 형식, {current_year}년)")
                    return True
                else:
                    print(f"❌ 올해 게시글 제외 ({current_year}년, {min_year}~{max_year}년 범위 외)")
                    return False
            
            # 기타 형식
            else:
                print(f"⚠️ 알 수 없는 날짜 형식: {date_text}")
                return True  # 알 수 없으면 포함
                
        except Exception as e:
            print(f"날짜 파싱 오류: {e}")
            return True  # 오류 시 포함
            
    except Exception as e:
        print(f"날짜 필터링 오류: {e}")
        return True  # 오류 시 포함

def is_notice_or_pinned(data):
    """공지/필독 게시글인지 확인하는 함수"""
    try:
        # 네이버 카페 실제 클래스 확인
        classes = data.get('class', [])
        if classes:
            class_str = ' '.join(classes)
            # board-notice 클래스가 있으면 공지/필독 게시글
            if 'board-notice' in class_str:
                print(f"board-notice 게시글 제외: {class_str}")
                return True
            
            # type_up 클래스가 있으면 상단 고정 게시글
            if 'type_up' in class_str:
                print(f"type_up 게시글 제외: {class_str}")
                return True
            
            # type_required 클래스가 있으면 필수 공지
            if 'type_required' in class_str:
                print(f"type_required 게시글 제외: {class_str}")
                return True
        
        # 말머리 확인
        category = data.find(class_=['category', 'prefix', 'badge'])
        if category:
            category_text = category.get_text().strip()
            if any(keyword in category_text for keyword in ['공지', '필독', 'NOTICE', 'PINNED']):
                return True
        
        # 제목에 공지/필독 키워드 확인
        title = data.find(class_=['title', 'subject'])
        if title:
            title_text = title.get_text().strip()
            if any(keyword in title_text for keyword in ['[공지]', '[필독]', '[NOTICE]']):
                return True
        
        # 특정 클래스나 속성 확인
        if data.find(class_=['notice', 'pinned', 'important']):
            return True
            
        return False
    except:
        return False

def safe_frame_switch(browser, frame_name='cafe_main'):
    """프레임 전환을 안전하게 처리하는 함수"""
    try:
        browser.switch_to.frame(frame_name)
        print(f"프레임 '{frame_name}' 전환 성공")
        return True
    except NoSuchFrameException:
        print(f"프레임 '{frame_name}'을 찾을 수 없습니다. 프레임 없이 진행합니다.")
        return False
    except Exception as e:
        print(f"프레임 전환 중 오류 발생: {e}")
        return False

clubid = '10197921'
menuid = '4082'
cafemenuurl = f'{baseurl}/ArticleList.nhn?search.clubid={clubid}&search.menuid={menuid}&search.boardtype=L&userDisplay=50'

i = 0
while(True):
    pageNum = i + 1
    userDisplay = 50

    browser.get(f'{cafemenuurl}&search.page={str(pageNum)}')
    
    # 페이지 완전 로딩 대기
    wait_for_page_load(browser)
    
    # 자연스러운 스크롤로 페이지 활성화
    human_like_scroll(browser)
    
    # 안전한 프레임 전환
    safe_frame_switch(browser, 'cafe_main')
    
    # 최소 대기로 동적 콘텐츠 로딩 보장
    random_delay(0.3, 0.8)

    soup = bs(browser.page_source, 'html.parser')
    
    # 다양한 방법으로 게시글 목록 찾기
    datas = []
    
    # 방법 1: 기존 방식
    article_boards = soup.find_all(class_ = 'article-board m-tcol-c')
    if len(article_boards) >= 2:
        soup_board = article_boards[1]
        datas = soup_board.select("#main-area > div:nth-child(4) > table > tbody > tr")
        print(f"페이지 {pageNum}: 방법1으로 {len(datas)}개 게시글 발견")
    
    # 방법 2: 다른 선택자들 시도
    if not datas:
        selectors_to_try = [
            "table.board-list tbody tr",
            ".board-list tbody tr", 
            "table tbody tr",
            ".article-list tr",
            "table.board tr",
            ".list tr",
            "tbody tr"
        ]
        
        for selector in selectors_to_try:
            datas = soup.select(selector)
            if datas and len(datas) > 1:  # 헤더 제외하고 실제 게시글이 있는지 확인
                print(f"페이지 {pageNum}: 방법2 ({selector})로 {len(datas)}개 게시글 발견")
                break
    
        # 방법 3: 모든 테이블에서 행이 많은 것 찾기
        if not datas:
            all_tables = soup.find_all('table')
            for i, table in enumerate(all_tables):
                rows = table.find_all('tr')
                if len(rows) > 5:  # 헤더 + 게시글들이 있을 것으로 예상
                    datas = rows
                    print(f"페이지 {pageNum}: 방법3 (테이블 {i})로 {len(datas)}개 행 발견")
                    break
        
        # board-notice, type_up 클래스가 있는 게시글들을 미리 필터링
        if datas:
            filtered_datas = []
            for data in datas:
                classes = data.get('class', [])
                if classes:
                    class_str = ' '.join(classes)
                    if 'board-notice' in class_str or 'type_up' in class_str:
                        print(f"페이지 {pageNum}: 공지/고정 게시글 미리 제외 - {class_str}")
                        continue
                filtered_datas.append(data)
            
            if filtered_datas:
                datas = filtered_datas
                print(f"페이지 {pageNum}: 공지/고정 게시글 필터링 후 {len(datas)}개 게시글 남음")

    for data in datas:
        # 공지/필독 게시글 제외
        if is_notice_or_pinned(data):
            print(f"페이지 {pageNum}: 공지/필독 게시글 제외")
            continue
        
        # 2024년~2025년 범위 내 게시글만 포함
        if not is_within_date_range(data, min_year=2024, max_year=2025):
            print(f"페이지 {pageNum}: 2024~2025년 범위 외 게시글 제외")
            continue
            
        article_info = data.select(".article")
        
        if not article_info:
            print(f"페이지 {pageNum}: 게시글 정보를 찾을 수 없습니다.")
            continue
            
        article_href = article_info[0].attrs['href']
        
        # URL이 이미 완전한 URL인지 확인
        if article_href.startswith('http'):
            # 이미 완전한 URL이면 그대로 사용
            pass
        else:
            # 상대 경로면 baseurl 추가
            article_href = f'{baseurl}{article_href}'
        
        print(f"게시글 URL: {article_href}")

        browser.get(article_href)
        
        # 페이지 완전 로딩 대기
        wait_for_page_load(browser)
        
        # 자연스러운 스크롤
        human_like_scroll(browser)
        
        # 안전한 프레임 전환
        safe_frame_switch(browser, 'cafe_main')
        
        # 최소 대기
        random_delay(0.2, 0.6)
        
        article_soup = bs(browser.page_source, 'html.parser')
        data = article_soup.find('div', class_='ArticleContentBox')
        
        if data is None:
            print(f"게시글 데이터를 찾을 수 없습니다: {article_href}")
            browser.back()
            random_delay(1, 2)
            continue
        
        # 댓글 크롤링
        print(f"댓글 크롤링 시작: {article_href}")
        comments = crawl_comments(article_soup, article_href)
        print(f"댓글 {len(comments)}개 크롤링 완료")

        article_title = data.find("h3", {"class" : "title_text"})
        article_date = data.find("span", {"class": "date"})
        article_content = data.find("div", {"class": "se-main-container"})
        article_author = data.find("button", {"class": "nickname"})

        if article_title == None :
            article_title = "null"
        else:
            article_title = article_title.text.strip()

        if article_date == None:
            article_date="null"
        else:
            article_date_str = article_date.text.strip()
            article_date_obj = datetime.strptime(article_date_str, '%Y.%m.%d. %H:%M')
            article_date = article_date_obj.strftime("%Y-%m-%d %H:%M:%S")

        if article_content is None:
            article_content = "null"
        else:
            article_content = article_content.text.strip()
            article_content = " ".join(re.split(r"\s+", article_content, flags=re.UNICODE))

        if article_author is None:
            article_author = "null"
        else:
            article_author = article_author.text.strip()

        # 댓글 데이터를 CSV 형식으로 변환
        comments_formatted = format_comments_for_csv(comments)
        
        # CSV 헤더 작성 (첫 번째 게시글에서만)
        import os
        if not os.path.exists('test.csv'):
            f = open(f'test.csv', 'w', newline='', encoding = "utf-8")
            wr = csv.writer(f)
            wr.writerow([
                '제목', 
                '작성자', 
                '작성일', 
                'URL', 
                '본문',
                '댓글데이터', 
                '댓글개수'
            ])
            f.close()
        
        # 게시글과 댓글 데이터를 함께 저장
        f = open(f'test.csv', 'a+', newline='', encoding = "utf-8")
        wr = csv.writer(f)
        wr.writerow([
            article_title, 
            article_author, 
            article_date, 
            article_href, 
            article_content,
            comments_formatted,  # 댓글 데이터 추가
            len(comments)  # 댓글 개수 추가
        ])
        f.close()
        
        print(f"게시글과 댓글 {len(comments)}개를 test.csv에 저장 완료")

        browser.back()
        random_delay(0.2, 0.5)  # 빠른 대기
    
    # 게시글이 없거나 2025년 이후 게시글이 많으면 종료
    if not datas:
        print(f"페이지 {pageNum}에 게시글이 없습니다. 크롤링 종료.")
        break
    
    # 2024~2025년 범위 외 게시글이 연속으로 많이 나오면 종료
    out_of_range_count = 0
    for data in datas[:5]:  # 처음 5개 게시글만 확인
        if not is_within_date_range(data, min_year=2024, max_year=2025):
            out_of_range_count += 1
    
    if out_of_range_count >= 3:  # 5개 중 3개 이상이 범위 외면
        print(f"페이지 {pageNum}: 2024~2025년 범위 외 게시글이 많아 크롤링 종료.")
        break
    
    # 페이지 간 빠른 대기
    random_delay(0.5, 1.0)
    i += 1  # 다음 페이지로 이동

browser.close()