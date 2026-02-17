import BottomTabBar from '@/components/BottomTabBar';

/**
 * 탭 그룹 레이아웃
 * 하단 5탭이 표시되는 메인 영역
 */
export default function TabsLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <>
            {children}
            <BottomTabBar />
        </>
    );
}
