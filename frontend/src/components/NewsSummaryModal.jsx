import React, { useEffect, useState } from 'react';
import { X, ExternalLink, Bot, Loader2, Calendar } from 'lucide-react';
import Markdown from 'react-markdown';

const NewsSummaryModal = ({ isOpen, onClose, article, summary, isLoading }) => {
    if (!isOpen || !article) return null;

    // Prevent scrolling when modal is open
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [isOpen]);

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />

            {/* Modal Content */}
            <div className="relative w-full max-w-2xl bg-white dark:bg-[#0F1115] border border-slate-200 dark:border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-200">

                {/* Header with Image */}
                <div className="relative h-48 bg-slate-100 dark:bg-gray-800 shrink-0">
                    <img
                        src={article.image_url || '/default-news.png'}
                        alt={article.headline}
                        className="w-full h-full object-cover opacity-90"
                        onError={(e) => { e.target.src = '/default-news.png'; }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />

                    <button
                        onClick={onClose}
                        className="absolute top-4 right-4 p-2 bg-black/40 hover:bg-black/60 backdrop-blur-md rounded-full text-white transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>

                    <div className="absolute bottom-4 left-6 right-6">
                        <div className="flex items-center gap-2 mb-2 text-white/80 text-xs font-semibold uppercase tracking-wider">
                            <span className={`px-2 py-0.5 rounded-full bg-white/20 backdrop-blur-sm border border-white/10 ${article.sentiment === 'positive' ? 'text-emerald-300' :
                                article.sentiment === 'negative' ? 'text-rose-300' : 'text-slate-200'
                                }`}>
                                {article.sentiment || 'News'}
                            </span>
                            <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {article.timestamp}
                            </span>
                        </div>
                        <h2 className="text-xl md:text-2xl font-bold text-white leading-tight shadow-black drop-shadow-lg line-clamp-2">
                            {article.headline}
                        </h2>
                    </div>
                </div>

                {/* Body */}
                <div className="p-6 overflow-y-auto custom-scrollbar">

                    <div className="bg-gradient-to-br from-blue-50/50 via-purple-50/30 to-blue-50/50 dark:from-blue-900/10 dark:via-purple-900/10 dark:to-blue-900/10 border border-blue-100 dark:border-blue-500/10 rounded-2xl p-5 mb-6">
                        <div className="flex items-center gap-2 mb-4">
                            <div className="p-1.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg shadow-lg shadow-blue-500/20">
                                <Bot className="w-5 h-5" />
                            </div>
                            <h3 className="text-sm font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent uppercase tracking-wide">
                                AI Summary
                            </h3>
                        </div>

                        {isLoading ? (
                            <div className="flex flex-col items-center justify-center py-8 space-y-3">
                                <Loader2 className="w-8 h-8 text-blue-500 dark:text-purple-400 animate-spin" />
                                <p className="text-sm text-slate-500 dark:text-gray-400 animate-pulse">Generating summary...</p>
                            </div>
                        ) : (
                            <div className="prose dark:prose-invert prose-sm max-w-none text-slate-700 dark:text-gray-300">
                                <Markdown>
                                    {summary}
                                </Markdown>
                            </div>
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="p-6 pt-0 mt-auto bg-white dark:bg-[#0F1115]">
                    <a
                        href={article.link}
                        target="_blank"
                        rel="noreferrer"
                        className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-blue-600/20 transition-all active:scale-[0.98]"
                    >
                        Read Full Article <ExternalLink className="w-4 h-4 ml-1" />
                    </a>
                </div>

            </div>
        </div>
    );
};

export default NewsSummaryModal;
