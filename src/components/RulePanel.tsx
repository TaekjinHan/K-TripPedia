/**
 * RulePanel -- 규칙 표시 패널
 */
import styles from './RulePanel.module.css';
import { RULE_LABELS } from '@/lib/constants';

interface RuleItem {
    id: string;
    rule_type: string;
    note_short: string | null;
    value_int: number | null;
    value_text: string | null;
}

interface RulePanelProps {
    rules: RuleItem[];
}

function formatRuleValue(rule: RuleItem): string {
    if (rule.note_short) return rule.note_short;
    if (rule.value_int !== null) return `${rule.value_int}`;
    if (rule.value_text) return rule.value_text;
    return '';
}

export default function RulePanel({ rules }: RulePanelProps) {
    if (rules.length === 0) return null;

    return (
        <div className={styles.panel}>
            <h3 className={styles.title}>ルール / 注意点</h3>
            <ul className={styles.list}>
                {rules.map((rule) => {
                    const label = RULE_LABELS[rule.rule_type]?.ja ?? rule.rule_type;
                    const value = formatRuleValue(rule);

                    return (
                        <li key={rule.id} className={styles.item}>
                            <span className={styles.ruleLabel}>{label}</span>
                            {value && <span className={styles.ruleValue}>{value}</span>}
                        </li>
                    );
                })}
            </ul>
        </div>
    );
}
