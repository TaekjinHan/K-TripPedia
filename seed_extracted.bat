@echo off
chcp 65001
echo 🚀 추출된 데이터를 Supabase에 시딩 중입니다...
call npx tsx scripts/seed-extracted-data.ts "C:\Users\Taekjin Hahn\.antigravity\HitoriOk(ひとりOK)\YouTube_SingleCh_Parsing\Extracted_Places_Data_Geocoded.xlsx"
pause
