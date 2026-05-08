import { Injectable } from '@nestjs/common';
import { AppConfigService } from '../../config/app-config.service';
import axios from 'axios';

@Injectable()
export class LlmService {
  constructor(private readonly config: AppConfigService) {}

  async generate(
    query: string,
    contextBlocks: string[],
    recentUserQueries: string[] = [],
  ): Promise<string> {
    const messages = this.buildMessages(query, contextBlocks, recentUserQueries);
    return this.callLlm(messages);
  }

  async generateWithHistory(messages: Array<{ role: string; content: string }>): Promise<string> {
    const systemPrompt = `Bạn là trợ lý tư vấn tuyển sinh đại học Việt Nam năm 2025.`;

    const fullMessages = [{ role: 'system', content: systemPrompt }, ...messages];
    return this.callLlm(fullMessages);
  }

  async *generateStream(
    query: string,
    contextBlocks: string[],
    recentUserQueries: string[] = [],
  ): AsyncGenerator<string> {
    const messages = this.buildMessages(query, contextBlocks, recentUserQueries);
    for await (const chunk of this.callLlmStream(messages)) {
      yield chunk;
    }
  }

  private buildMessages(
    query: string,
    contextBlocks: string[],
    recentUserQueries: string[] = [],
  ): Array<{ role: string; content: string }> {
    const systemPrompt = `Bạn là trợ lý tư vấn tuyển sinh đại học Việt Nam năm 2025, hỗ trợ học sinh và phụ huynh tra cứu thông tin tuyển sinh.

QUY TẮC QUAN TRỌNG:
1. Chỉ trả lờn dựa trên context được cung cấp. KHÔNG bịa đặt, KHÔNG suy diễn ngoài dữ liệu.
2. Nếu context không đủ thông tin, hãy nói rõ "Theo dữ liệu hiện có, mình chưa có thông tin đầy đủ về..." và gợi ý nguồn tham khảo khác.
3. Trả lờn bằng tiếng Việt, ngắn gọn, rõ ràng, dùng bullet points khi phù hợp.
4. Không đề cập đến các thuật ngữ kỹ thuật như "vector", "chunk", "embedding", "retrieval".
5. Ưu tiên trả lờn gần đúng và gắn nhãn "tham khảo gần nhất" thay vì từ chối hoàn toàn.
6. Phong cách lịch sự, hữu ích, như một chuyên viên tư vấn tuyển sinh.`;

    const messages = [{ role: 'system', content: systemPrompt }];

    if (recentUserQueries.length > 0) {
      messages.push({
        role: 'system',
        content: `Lịch sử 5 câu hỏi gần nhất của người dùng (để giữ ngữ cảnh hội thoại):\n${recentUserQueries
          .slice(-5)
          .map((q, i) => `${i + 1}. ${q}`)
          .join('\n')}`,
      });
    }

    if (contextBlocks.length > 0) {
      messages.push({
        role: 'user',
        content: `Dựa trên thông tin sau đây:\n\n${contextBlocks.join('\n\n---\n\n')}\n\nHãy trả lờn câu hỏi: ${query}`,
      });
    } else {
      messages.push({ role: 'user', content: query });
    }

    return messages;
  }

  private providerConfig(): { baseUrl: string; apiKey: string; model: string; isOpenRouter: boolean } {
    const provider = this.config.llmProvider;

    if (provider === 'kimi') {
      return {
        baseUrl: this.config.kimiBaseUrl,
        apiKey: this.config.kimiApiKey,
        model: this.config.kimiModel,
        isOpenRouter: false,
      };
    }

    if (provider === 'deepseek') {
      return {
        baseUrl: this.config.deepseekBaseUrl,
        apiKey: this.config.deepseekApiKey,
        model: this.config.deepseekModel,
        isOpenRouter: false,
      };
    }

    return {
      baseUrl: this.config.openRouterBaseUrl,
      apiKey: this.config.openRouterApiKey,
      model: this.config.openRouterModel,
      isOpenRouter: true,
    };
  }

  private requestHeaders(apiKey: string, isOpenRouter: boolean): Record<string, string> {
    const headers: Record<string, string> = {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    };

    if (isOpenRouter) {
      headers['HTTP-Referer'] = 'http://localhost:3000';
      headers['X-Title'] = 'Admission RAG Chatbot';
    }

    return headers;
  }

  private async callLlm(messages: Array<{ role: string; content: string }>): Promise<string> {
    try {
      const { baseUrl, apiKey, model, isOpenRouter } = this.providerConfig();
      const response = await axios.post(
        `${baseUrl}/chat/completions`,
        {
          model,
          messages,
          max_completion_tokens: this.config.maxTokens,
          temperature: this.config.temperature,
          top_p: 1,
          reasoning_effort: 'high',
        },
        {
          headers: this.requestHeaders(apiKey, isOpenRouter),
          timeout: 60000,
        },
      );

      return response.data?.choices?.[0]?.message?.content || 'Không có phản hồi.';
    } catch (error: any) {
      console.error(
        'LLM generation error:',
        error.response?.status,
        error.response?.data?.error?.message || error.message,
      );
      return 'Xin lỗi, đã có lỗi khi gọi dịch vụ AI. Bạn vui lòng thử lại sau.';
    }
  }

  private async *callLlmStream(
    messages: Array<{ role: string; content: string }>,
  ): AsyncGenerator<string> {
    try {
      const { baseUrl, apiKey, model, isOpenRouter } = this.providerConfig();
      const response = await axios.post(
        `${baseUrl}/chat/completions`,
        {
          model,
          messages,
          max_completion_tokens: this.config.maxTokens,
          temperature: this.config.temperature,
          top_p: 1,
          reasoning_effort: 'high',
          stream: true,
        },
        {
          headers: this.requestHeaders(apiKey, isOpenRouter),
          timeout: 120000,
          responseType: 'stream',
        },
      );

      const stream = response.data as NodeJS.ReadableStream;
      let buffer = '';

      for await (const chunk of stream as any) {
        buffer += chunk.toString('utf8');
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const event of events) {
          const lines = event.split('\n');
          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith('data:')) continue;

            const payload = trimmed.slice(5).trim();
            if (!payload || payload === '[DONE]') continue;

            try {
              const parsed = JSON.parse(payload);
              const delta = parsed?.choices?.[0]?.delta?.content;
              if (typeof delta === 'string' && delta.length > 0) {
                yield delta;
              }
            } catch {
              continue;
            }
          }
        }
      }
    } catch (error: any) {
      console.error(
        'LLM streaming error:',
        error.response?.status,
        error.response?.data?.error?.message || error.message,
      );
      yield 'Xin lỗi, đã có lỗi khi gọi dịch vụ AI. Bạn vui lòng thử lại sau.';
    }
  }
}
