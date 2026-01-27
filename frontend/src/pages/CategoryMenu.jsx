import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, ArrowRight, Shield, TrendingUp, DollarSign, Building, Globe, Zap, BarChart3, Briefcase } from 'lucide-react';

const CATEGORIES = {
    Business: [
        { id: 'Economy', label: 'Economy', icon: Globe },
        { id: 'Companies', label: 'Companies', icon: Building },
        { id: 'Mutual Funds', label: 'Mutual Funds', icon: DollarSign },
        { id: 'Personal Finance', label: 'Personal Finance', icon: Shield },
        { id: 'IPO', label: 'IPO', icon: Zap },
        { id: 'Startup', label: 'Startup', icon: TrendingUp },
        { id: 'Real Estate', label: 'Real Estate', icon: Building },
        { id: 'Banking', label: 'Banking', icon: Briefcase },
    ],
    Markets: [
        { id: 'Stocks', label: 'Stocks', icon: BarChart3 },
        { id: 'Technical Analysis', label: 'Technical Analysis', icon: TrendingUp },
        { id: 'Equity Research', label: 'Equity Research', icon: Search },
        { id: 'Commodities', label: 'Commodities', icon: Package },
        { id: 'Currency', label: 'Currency', icon: DollarSign },
        { id: 'Gold Rate', label: 'Gold Rate', icon: Zap }, // Using Zap as placeholder/gold
        { id: 'Silver Rate', label: 'Silver Rate', icon: Zap },
        { id: 'AQI', label: 'AQI', icon: Cloud },
        { id: 'Earnings', label: 'Earnings', icon: BarChart3 },
    ]
};

// Helper for icons that might not be imported or standard
function Search(props) { return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg> }
function Package(props) { return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m7.5 4.27 9 5.15" /><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" /><path d="m3.3 7 8.7 5 8.7-5" /><path d="M12 22v-9" /></svg> }
function Cloud(props) { return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.5 19c0-1.7-1.3-3-3-3h-11a4 4 0 0 1-3.8-5 5 5 0 0 1 9.8-1.2 3 3 0 0 1 6 2.2" /></svg> }


const CategoryMenu = () => {
    const navigate = useNavigate();
    const [selected, setSelected] = useState([]);

    useEffect(() => {
        // Load existing preferences if any
        const userEmail = localStorage.getItem('userEmail');
        const storageKey = userEmail ? `userCategories_${userEmail}` : 'userCategories';
        const saved = localStorage.getItem(storageKey);
        if (saved) {
            setSelected(JSON.parse(saved));
        }
    }, []);

    const toggleCategory = (id) => {
        if (selected.includes(id)) {
            setSelected(selected.filter(item => item !== id));
        } else {
            setSelected([...selected, id]);
        }
    };

    const handleContinue = () => {
        const userEmail = localStorage.getItem('userEmail');
        const storageKey = userEmail ? `userCategories_${userEmail}` : 'userCategories';
        localStorage.setItem(storageKey, JSON.stringify(selected));
        navigate('/'); // Go to Dashboard
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-[#0a0c10] text-slate-900 dark:text-white p-6 flex flex-col items-center justify-center relative overflow-hidden">
            {/* Background Glows */}
            <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[100px] pointer-events-none" />
            <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[100px] pointer-events-none" />

            <div className="max-w-4xl w-full relative z-10">
                <div className="text-center mb-10">
                    <h1 className="text-4xl font-black mb-4 tracking-tight">Personalize Your Feed</h1>
                    <p className="text-slate-500 dark:text-gray-400 text-lg">Select the topics you're interested in.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
                    {/* Business Column */}
                    <div className="space-y-4">
                        <h2 className="text-xl font-bold border-b border-slate-200 dark:border-white/10 pb-2 mb-4 text-blue-600 dark:text-blue-400 uppercase tracking-widest text-xs">Business</h2>
                        <div className="grid grid-cols-2 gap-3">
                            {CATEGORIES.Business.map(cat => {
                                const isSelected = selected.includes(cat.id);
                                const Icon = cat.icon;
                                return (
                                    <button
                                        key={cat.id}
                                        onClick={() => toggleCategory(cat.id)}
                                        className={`p-4 rounded-xl border flex flex-col items-center justify-center gap-3 transition-all duration-200 group relative overflow-hidden ${isSelected
                                            ? 'bg-blue-600 border-blue-600 text-white shadow-lg shadow-blue-500/30'
                                            : 'bg-white dark:bg-[#13161b] border-slate-200 dark:border-white/5 hover:border-blue-500/50 hover:bg-slate-50 dark:hover:bg-white/5'
                                            }`}
                                    >
                                        <div className={`p-2 rounded-full ${isSelected ? 'bg-white/20' : 'bg-slate-100 dark:bg-white/5 group-hover:scale-110 transition-transform'}`}>
                                            <Icon className="w-5 h-5" />
                                        </div>
                                        <span className="font-semibold text-sm">{cat.label}</span>
                                        {isSelected && (
                                            <div className="absolute top-2 right-2">
                                                <Check className="w-4 h-4" />
                                            </div>
                                        )}
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Markets Column */}
                    <div className="space-y-4">
                        <h2 className="text-xl font-bold border-b border-slate-200 dark:border-white/10 pb-2 mb-4 text-emerald-600 dark:text-emerald-400 uppercase tracking-widest text-xs">Markets</h2>
                        <div className="grid grid-cols-2 gap-3">
                            {CATEGORIES.Markets.map(cat => {
                                const isSelected = selected.includes(cat.id);
                                const Icon = cat.icon;
                                return (
                                    <button
                                        key={cat.id}
                                        onClick={() => toggleCategory(cat.id)}
                                        className={`p-4 rounded-xl border flex flex-col items-center justify-center gap-3 transition-all duration-200 group relative overflow-hidden ${isSelected
                                            ? 'bg-emerald-600 border-emerald-600 text-white shadow-lg shadow-emerald-500/30'
                                            : 'bg-white dark:bg-[#13161b] border-slate-200 dark:border-white/5 hover:border-emerald-500/50 hover:bg-slate-50 dark:hover:bg-white/5'
                                            }`}
                                    >
                                        <div className={`p-2 rounded-full ${isSelected ? 'bg-white/20' : 'bg-slate-100 dark:bg-white/5 group-hover:scale-110 transition-transform'}`}>
                                            <Icon className="w-5 h-5" />
                                        </div>
                                        <span className="font-semibold text-sm">{cat.label}</span>
                                        {isSelected && (
                                            <div className="absolute top-2 right-2">
                                                <Check className="w-4 h-4" />
                                            </div>
                                        )}
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                </div>

                <div className="fixed bottom-0 left-0 right-0 p-6 bg-white/80 dark:bg-[#0a0c10]/80 backdrop-blur-xl border-t border-slate-200 dark:border-white/10 flex justify-center z-50">
                    <button
                        onClick={handleContinue}
                        className="w-full max-w-md bg-blue-600 hover:bg-blue-700 text-white text-lg font-bold py-4 rounded-2xl shadow-xl shadow-blue-500/20 transition-all active:scale-95 flex items-center justify-center gap-2"
                    >
                        Continue to Dashboard <ArrowRight className="w-5 h-5" />
                    </button>
                </div>
                <div className="h-24"></div> {/* Spacer for fixed bottom bar */}
            </div>
        </div>
    );
};

export default CategoryMenu;
