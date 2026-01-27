import React, { useEffect } from 'react';
import { X, AlertTriangle } from 'lucide-react';

const DisclaimerModal = ({ isOpen, onClose }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/80 backdrop-blur-sm transition-opacity"
            />

            {/* Modal Content */}
            <div className="relative w-full max-w-md max-h-[90vh] overflow-y-auto bg-white dark:bg-[#0F1115] border border-slate-200 dark:border-white/10 rounded-2xl shadow-2xl animate-in fade-in zoom-in-95 duration-200">

                {/* Header */}
                <div className="p-6 pb-2 flex items-center gap-3">
                    <div className="p-2 bg-orange-100 dark:bg-orange-900/20 rounded-xl text-orange-600 dark:text-orange-500">
                        <AlertTriangle className="w-6 h-6" />
                    </div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Disclaimer</h2>
                </div>

                {/* Body */}
                <div className="px-6 py-4">
                    <p className="text-slate-600 dark:text-gray-300 leading-relaxed text-sm">
                        The stock market information, news summaries, and analysis provided by MarketPulseAI are for
                        <span className="font-bold text-slate-900 dark:text-white"> educational and informational purposes only</span>.
                        <br /><br />
                        We are not a SEBI registered investment advisor. Please consult with a certified financial advisor before making any investment decisions.
                        <br /><br />
                        <span className="font-semibold text-rose-500">
                            Trading in securities involves high risk. Use this platform at your own risk.
                        </span>
                    </p>
                </div>

                {/* Footer */}
                <div className="p-6 pt-2 flex justify-end">
                    <button
                        onClick={onClose}
                        className="flex items-center gap-2 px-6 py-2.5 bg-slate-900 dark:bg-white text-white dark:text-black rounded-xl font-bold hover:opacity-90 transition-opacity"
                    >
                        I Understand
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DisclaimerModal;
