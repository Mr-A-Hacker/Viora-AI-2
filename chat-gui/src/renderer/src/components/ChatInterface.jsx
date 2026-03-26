import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import ChatHeader from './ChatHeader';
import ConnectionBar from './ConnectionBar';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import ChatSidebar from './ChatSidebar';
import VirtualKeyboard from './VirtualKeyboard';
import { motion } from 'framer-motion';

import { useWebSocket } from '../contexts/WebSocketContext.jsx';
import { useKeyboardSettings } from '../contexts/KeyboardContext.jsx';

export default function ChatInterface() {
    const location = useLocation();
    const {
        connStatus,
        connect,
        chatConnStatus,
        messages,
        setMessages,
        streamText,
        streaming,
        sendMessage,
        conversations,
        currentConvId,
        setCurrentConvId,
        createConversation,
        deleteConversation,
        fetchConversations,
        thinking,
        toggleVoice,
        isRecording,
        addEventListener,
    } = useWebSocket();

    const [sidebarOpen, setSidebarOpen] = useState(false);
    const { keyboardEnabled, focusState, setFocusState, focusedElementRef, syncInputValueRef } = useKeyboardSettings();
    const showInlineKeyboard = keyboardEnabled && focusState?.isChatInput === true;

    const closeKeyboard = useCallback(() => {
        setFocusState(null);
        focusedElementRef.current = null;
    }, [setFocusState, focusedElementRef]);

    const handleChatAreaPointerDown = useCallback(
        (e) => {
            if (!focusState?.isChatInput) return;
            const target = e.target;
            if (target?.closest?.('[data-virtual-keyboard]')) return;
            if (target?.closest?.('[data-chat-input-bar]')) return;
            if (target?.closest?.('[data-chat-messages]')) return;
            closeKeyboard();
        },
        [focusState?.isChatInput, closeKeyboard]
    );

    const send = useCallback(
        async (text, images = []) => {
            let activeConvId = currentConvId;
            if (!activeConvId) {
                const conv = await createConversation();
                if (conv) {
                    activeConvId = conv.id;
                    setCurrentConvId(conv.id);
                } else {
                    console.error("Failed to create conversation");
                    return;
                }
            }
            setMessages((prev) => [...prev, { role: 'user', text }]);
            sendMessage('send', { message: text, images, conv_id: activeConvId, thinking });
        },
        [sendMessage, setMessages, currentConvId, createConversation, setCurrentConvId, thinking]
    );

    useEffect(() => {
        if (!currentConvId && conversations.length > 0) {
            setCurrentConvId(conversations[0].id);
        }
    }, [currentConvId, conversations, setCurrentConvId]);

    useEffect(() => {
        fetchConversations();
        const interval = setInterval(fetchConversations, 15000);
        return () => clearInterval(interval);
    }, [fetchConversations]);

    useEffect(() => {
        if (chatConnStatus === 'connected' && location.state?.prompt && location.state?.image && currentConvId) {
            const { prompt, image } = location.state;
            window.history.replaceState({}, document.title);
            send(prompt, [image]);
        }
    }, [chatConnStatus, location.state, send, currentConvId]);

    useEffect(() => {
        const remove = addEventListener('voice_transcription', async (data) => {
            const text = (data.text || '').trim();
            if (!text) return;
            let convId = currentConvId;
            if (!convId && conversations.length > 0) convId = conversations[0].id;
            if (!convId) {
                const conv = await createConversation();
                if (conv) {
                    setCurrentConvId(conv.id);
                    convId = conv.id;
                }
            }
            if (convId) sendMessage('send', { message: text, conv_id: convId, thinking });
        });
        return remove;
    }, [addEventListener, currentConvId, conversations, createConversation, setCurrentConvId, sendMessage, thinking]);

    const abort = useCallback(() => {
        sendMessage('abort');
    }, [sendMessage]);

    const reset = useCallback(() => {
        sendMessage('reset');
    }, [sendMessage]);

    const handleNewChat = async () => {
        const conv = await createConversation();
        if (conv) setCurrentConvId(conv.id);
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="w-full h-full mx-auto flex bg-[var(--bg)] relative overflow-hidden"
        >
            <ChatSidebar
                isOpen={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
                conversations={conversations}
                currentConvId={currentConvId}
                setCurrentConvId={setCurrentConvId}
                createConversation={createConversation}
                deleteConversation={deleteConversation}
            />

            <div
                className="flex-1 flex flex-col h-full min-w-0 min-h-0 touch-pan-y"
                onPointerDown={handleChatAreaPointerDown}
            >
                <ChatHeader
                    connected={connStatus === 'connected'}
                    onReset={reset}
                    sidebarOpen={sidebarOpen}
                    onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
                    onCloseKeyboard={closeKeyboard}
                />
                {connStatus !== 'connected' && <ConnectionBar status={connStatus} onRetry={connect} />}
                <MessageList
                    messages={messages}
                    streaming={streaming}
                    streamText={streamText}
                />
                <ChatInput
                    onSend={send}
                    onAbort={abort}
                    onMicPress={() => toggleVoice({ transcriptionOnly: true })}
                    isRecording={isRecording}
                    streaming={streaming}
                    disabled={connStatus !== 'connected'}
                />
                <VirtualKeyboard visible={showInlineKeyboard} mode="inline" focusedElementRef={focusedElementRef} syncInputValueRef={syncInputValueRef} />
            </div>

            <div className="ambient-bg fixed inset-0 -z-10 overflow-hidden pointer-events-none">
                <div className="blob-1 absolute w-[500px] h-[500px] rounded-full opacity-20 blur-[100px]" />
                <div className="blob-2 absolute w-[400px] h-[400px] rounded-full opacity-15 blur-[80px] top-1/3 right-1/4" />
                <div className="blob-3 absolute w-[350px] h-[350px] rounded-full opacity-10 blur-[60px] bottom-1/4 left-1/3" />
            </div>
        </motion.div>
    );
}
