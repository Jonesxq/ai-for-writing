# official_proj/services/novel_service.py

class NovelService:

    def __init__(
        self,
        novel_dao,
        chapter_dao,
        plot_summary_dao,
        character_state_dao,
        plot_memory_service,
        prompt_builder,
        writer_agent,
        summary_agent,
        state_agent
    ):
        self.novel_dao = novel_dao
        self.chapter_dao = chapter_dao
        self.plot_summary_dao = plot_summary_dao
        self.character_state_dao = character_state_dao
        self.plot_memory_service = plot_memory_service

        self.prompt_builder = prompt_builder
        self.writer_agent = writer_agent
        self.summary_agent = summary_agent
        self.state_agent = state_agent

    def write_next_chapter(
            self,
            novel_id: str,
            chapter_goal: str
    ):
        """
        写下一章完整流程：
        1. 剧情回忆（Milvus）
        2. 构建 Prompt
        3. LLM 写章节
        4. 章节摘要 & 关键事件
        5. 更新人物状态（历史追加）
        6. MySQL 落库
        7. 向量记忆写入
        """

        # ---------- 1️⃣ 获取小说 & 上一章 ----------
        novel = self.novel_dao.get(novel_id)
        last_chapter = self.chapter_dao.get_last_chapter(novel_id)

        chapter_number = 1 if not last_chapter else last_chapter.chapter_number + 1

        # ---------- 2️⃣ 剧情回忆（Milvus） ----------
        memories = self.plot_memory_service.recall_relevant_plots(
            novel_id=novel_id,
            current_chapter_goal=chapter_goal,
            top_k=5
        )

        # ---------- 3️⃣ 构建 Prompt ----------
        prompt = self.prompt_builder.build_chapter_prompt(
            novel=novel,
            chapter_number=chapter_number,
            chapter_goal=chapter_goal,
            memories=memories
        )

        # ---------- 4️⃣ CrewAI 写章节 ----------
        chapter_text = self.writer_agent.run(prompt)

        # ---------- 5️⃣ 保存 Chapter（MySQL） ----------
        chapter = self.chapter_dao.create(
            novel_id=novel_id,
            chapter_number=chapter_number,
            title=f"第{chapter_number}章",
            content=chapter_text
        )

        # ---------- 6️⃣ 章节摘要 & 关键事件 ----------
        plot_summary = self.summary_agent.run(chapter_text)

        summary_record = self.plot_summary_dao.create(
            novel_id=novel_id,
            chapter_id=chapter.id,
            key_events=plot_summary["key_events"],
            consequences=plot_summary["consequences"]
        )

        # ---------- 7️⃣ 更新人物状态（永远追加） ----------
        character_states = self.state_agent.run(
            chapter_text=chapter_text
        )

        for state in character_states:
            self.character_state_dao.create(
                character_id=state["character_id"],
                chapter_id=chapter.id,
                location=state["location"],
                emotion=state["emotion"],
                goal=state["goal"],
                relationships=state["relationships"]
            )

        # ---------- 8️⃣ 向量记忆写入（Milvus） ----------
        plot_summary_text = "\n".join(plot_summary["key_events"])

        self.plot_memory_service.save_plot_memory(
            novel_id=novel_id,
            chapter_number=chapter_number,
            plot_summary_text=plot_summary_text
        )

        return chapter

