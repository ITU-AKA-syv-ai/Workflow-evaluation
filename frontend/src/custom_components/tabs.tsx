import type { ReactNode } from 'react';
import { useState } from 'react';

import './tabs.css'

interface Tab {
    label: string;
    component: ReactNode;
}

interface TabsProps {
      tabs: Tab[]
}
export default function Tabs({tabs}: TabsProps) {
    const [tabIndex, setTabIndex] = useState<number>(0);

    const tabButtons = tabs.map((x: Tab, index: number) => {
                        const className = (index == tabIndex) ? " tabButtonActive" : "tabButton";
                        return <button className={className} key={x.label} onClick={_ => setTabIndex(index)}>{x.label}</button>
                     });
    return (
        <div>
            <div className="tabsContainerLabels">
                {tabButtons}
            </div>

            {tabs[tabIndex].component}
        </div>
    );
}

