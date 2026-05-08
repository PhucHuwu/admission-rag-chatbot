import { Controller, Post, Body, Res } from '@nestjs/common';
import { Response } from 'express';
import { ChatService } from './chat.service';
import { ChatRequestDto } from '../../common/dtos/request.dto';

@Controller('api/v1/chat')
export class ChatController {
  constructor(private readonly chatService: ChatService) {}

  @Post()
  async chat(@Body() dto: ChatRequestDto) {
    return this.chatService.answer(dto.query, dto.session_id, dto.university_code);
  }

  @Post('stream')
  async chatStream(@Body() dto: ChatRequestDto, @Res() res: Response): Promise<void> {
    res.setHeader('Content-Type', 'text/event-stream; charset=utf-8');
    res.setHeader('Cache-Control', 'no-cache, no-transform');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('X-Accel-Buffering', 'no');
    res.flushHeaders();

    const generator = this.chatService.answerStream(dto.query, dto.session_id, dto.university_code);

    try {
      for await (const item of generator) {
        if (item.type === 'chunk') {
          res.write(`data: ${JSON.stringify({ chunk: item.text })}\n\n`);
          continue;
        }

        res.write(
          `data: ${JSON.stringify({ done: true, session_id: item.session_id, used_chunks: item.used_chunks, data_sufficient: item.data_sufficient, note: item.note })}\n\n`,
        );
      }
    } catch (error: any) {
      res.write(`data: ${JSON.stringify({ error: error?.message || 'Streaming failed' })}\n\n`);
    } finally {
      res.end();
    }
  }
}
