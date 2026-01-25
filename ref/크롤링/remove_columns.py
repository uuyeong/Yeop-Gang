# -*- coding: utf-8 -*-
import pandas as pd
import os

# 스크립트 파일이 있는 디렉토리로 이동
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# 제거할 컬럼들
columns_to_remove = ['작성자', '작성일', 'URL', '댓글개수']

# test.csv 처리
print("test.csv 처리 중...")
df1 = pd.read_csv('test.csv', encoding='utf-8-sig')
df1 = df1.drop(columns=columns_to_remove)
df1.to_csv('test.csv', index=False, encoding='utf-8-sig')
print(f"test.csv 완료: {len(df1)}행 처리됨")

# N수게시판.csv 처리
print("N수게시판.csv 처리 중...")
df2 = pd.read_csv('N수게시판.csv', encoding='utf-8-sig')
df2 = df2.drop(columns=columns_to_remove)
df2.to_csv('N수게시판.csv', index=False, encoding='utf-8-sig')
print(f"N수게시판.csv 완료: {len(df2)}행 처리됨")

print("모든 파일 처리 완료!")

