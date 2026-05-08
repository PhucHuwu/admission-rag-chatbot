import { Injectable, Logger, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(PrismaService.name);
  private readonly dbDisabled =
    process.env.DISABLE_DB === 'true' ||
    process.env.DISABLE_DB === '1' ||
    !process.env.DATABASE_URL;

  async onModuleInit() {
    if (this.dbDisabled) {
      this.logger.warn('Skipping Prisma connection (DISABLE_DB enabled or DATABASE_URL missing).');
      return;
    }
    await this.$connect();
  }

  async onModuleDestroy() {
    if (this.dbDisabled) {
      return;
    }
    await this.$disconnect();
  }
}
