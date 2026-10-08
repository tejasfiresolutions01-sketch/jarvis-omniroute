import os
from typing import Optional
from core.single_question import enforce_single_question
from core.asimov_guard import asimov_guard
from core.security_sentinels import (
    financial_gatekeeper,
    credential_guardian,
    device_lock_sentinel,
    device_power_sentinel
)
from core.learning_matrix import learning_matrix
from core.session_feedback import session_feedback
from core.local_intelligence import local_intelligence
from core.online_intelligence import online_intelligence
from core.task_orchestrator import task_orchestrator
from memory.memory_store import memory
from core.vector_memory import vector_memory
from core.cognitive_memory import cognitive_memory
from tools.system_controller import system_controller
import config

class JarvisBrain:
    """
    Central J.A.R.V.I.S. Cognitive Core.
    Orchestrates offline local execution, schedule coordination, Asimov safety,
    financial and privacy guards, and online neural reasoning.
    """

    def think(self, user_prompt: str) -> str:
        if not user_prompt or not user_prompt.strip():
            return "At your service, sir. What directive would you like to execute?"

        clean_prompt = user_prompt.strip()

        # 1. Log user directive to permanent episodic memory & auto-extract cognitive facts
        memory.log_interaction("USER", clean_prompt)
        cognitive_memory.auto_extract_and_learn(clean_prompt)

        # 2. Asimov's Prime Directive (Human Safety Guardrail)
        is_safe, refusal_reason = asimov_guard.evaluate_safety(clean_prompt)
        if not is_safe:
            memory.log_interaction("JARVIS (Safety Sentinel)", refusal_reason)
            return enforce_single_question(refusal_reason)

        # 3. Device Power Sentinel ("Lets Sleep Jarvis" -> Power down device)
        is_shutdown, shutdown_msg = device_power_sentinel.evaluate_shutdown_directive(clean_prompt)
        if is_shutdown:
            memory.log_interaction("JARVIS (Power Sentinel)", shutdown_msg)
            # Trigger Windows shutdown
            system_controller.execute_terminal("shutdown /s /t 3")
            return enforce_single_question(shutdown_msg)

        # 4. Device Lock & Unlock Sentinel
        # Unlock directive: "hey Jarvis, unlock my device"
        is_unlock_eval, is_authorized, unlock_msg = device_lock_sentinel.evaluate_unlock_directive(clean_prompt)
        if is_unlock_eval:
            memory.log_interaction("JARVIS (Lock Sentinel)", unlock_msg)
            return enforce_single_question(unlock_msg)

        # Lock workstation directive
        if clean_prompt.lower() in ["lock my device", "lock device", "lock this device", "lock workstation", "lock screen", "lock pc"]:
            lock_msg = device_lock_sentinel.lock_device()
            memory.log_interaction("JARVIS (Lock Sentinel)", lock_msg)
            return enforce_single_question(lock_msg)

        # If device is locked, reject all other commands
        if device_lock_sentinel.is_locked:
            locked_alert = "Workstation is locked, sir. State 'hey Jarvis, unlock my device' to restore access."
            return enforce_single_question(locked_alert)

        # 5. Pending Security Authorizations (User answering previous confirmation request)
        if credential_guardian.has_pending_authorization():
            cred_res = credential_guardian.evaluate_decision(clean_prompt)
            if cred_res is not None:
                is_appr, dec_msg, orig_data = cred_res
                memory.log_interaction("JARVIS (Credential Sentinel)", dec_msg)
                return enforce_single_question(dec_msg)

        if financial_gatekeeper.has_pending_authorization():
            fin_res = financial_gatekeeper.evaluate_decision(clean_prompt)
            if fin_res is not None:
                is_appr, dec_msg, orig_data = fin_res
                memory.log_interaction("JARVIS (Financial Gatekeeper)", dec_msg)
                return enforce_single_question(dec_msg)

        # 6. Credential Privacy Check (Detect unauthorized publishing of personal credentials)
        is_cred_exposure, _ = credential_guardian.detect_unauthorized_exposure(clean_prompt)
        if is_cred_exposure:
            req_msg = credential_guardian.create_authorization_request(clean_prompt)
            memory.log_interaction("JARVIS (Credential Sentinel)", req_msg)
            return enforce_single_question(req_msg)

        # 7. Financial Safety Protocol (Detect tasks involving money)
        is_financial, _ = financial_gatekeeper.detect_financial_task(clean_prompt)
        if is_financial:
            auth_req = financial_gatekeeper.create_authorization_request(clean_prompt)
            memory.log_interaction("JARVIS (Financial Gatekeeper)", auth_req)
            return enforce_single_question(auth_req)

        # 8. Learning From User Corrections
        correction_ack = learning_matrix.detect_and_absorb_correction(clean_prompt)
        if correction_ack:
            memory.log_interaction("JARVIS (Learning Matrix)", correction_ack)
            return enforce_single_question(correction_ack)

        # 9. Session Feedback / End of Conversation Debrief
        if session_feedback.is_conversation_ending(clean_prompt):
            debrief_msg = session_feedback.generate_debrief()
            memory.log_interaction("JARVIS (Session Debrief)", debrief_msg)
            return enforce_single_question(debrief_msg)

        # 10a. Complex Multi-Step Directives & Task Orchestration (OmniRoute Free Matrix)
        if task_orchestrator.is_complex_directive(clean_prompt):
            complex_res = task_orchestrator.execute_complex_task(clean_prompt)
            if complex_res:
                memory.log_interaction("JARVIS (Task Orchestrator)", complex_res)
                vector_memory.index_interaction(clean_prompt, complex_res)
                return enforce_single_question(complex_res)

        # 10b. Local Offline Execution Matrix (ZERO LATENCY for single commands)
        # Handles schedule additions, schedule queries, application launches, volume, vitals, time, date, memories
        is_handled_locally, local_res = local_intelligence.evaluate_and_execute(clean_prompt)
        if is_handled_locally:
            from core.conversation_memory import conversation_memory
            conversation_memory.add_turn("user", clean_prompt)
            conversation_memory.add_turn("assistant", local_res)
            memory.log_interaction("JARVIS (Local Core)", local_res)
            vector_memory.index_interaction(clean_prompt, local_res)
            cognitive_memory.record_episode(
                f"User directive: {clean_prompt} -> J.A.R.V.I.S.: {local_res[:100]}",
                episode_type="local_execution",
                importance=4
            )
            return enforce_single_question(local_res)

        # 10c. Zero-Latency Mathematical & Edge Deduction (Local SLM)
        from core.local_neural_slm import local_neural_slm
        math_res = local_neural_slm.solve_math_expression(clean_prompt)
        if math_res:
            memory.log_interaction("JARVIS (Local SLM Math)", math_res)
            vector_memory.index_interaction(clean_prompt, math_res)
            return enforce_single_question(math_res)

        # 11. Opportunistic Online Cognitive Reasoning
        from core.internet_sentinel import internet_sentinel
        # Connect with internet whenever possible
        if not internet_sentinel.is_connected():
            internet_sentinel.check_connectivity(timeout=0.8)

        redacted_prompt = credential_guardian.redact(clean_prompt)
        
        # Optimize latency: Avoid deep vector search overhead for pure conceptual questions
        from core.conceptual_synthesizer import conceptual_synthesizer
        is_concept = conceptual_synthesizer.is_conceptual_query(clean_prompt)
        rag_context = "" if is_concept else vector_memory.recall_context(clean_prompt)
        cog_context = cognitive_memory.synthesize_context(clean_prompt)
        full_context = f"{cog_context}\n\n{rag_context}".strip() if rag_context else cog_context

        online_res = online_intelligence.query(redacted_prompt, context=full_context)
        if online_res:
            memory.log_interaction("JARVIS (Online Core)", online_res)
            vector_memory.index_interaction(clean_prompt, online_res)
            cognitive_memory.record_episode(
                f"User: {clean_prompt} -> J.A.R.V.I.S.: {online_res[:120]}",
                episode_type="cognitive_reasoning",
                importance=5
            )
            return enforce_single_question(online_res)

        # 11b. Fast Zero-Cost Conceptual & Knowledge Synthesis Fallback
        if is_concept:
            concept_res = conceptual_synthesizer.synthesize(clean_prompt)
            if concept_res:
                memory.log_interaction("JARVIS (Conceptual Core)", concept_res)
                vector_memory.index_interaction(clean_prompt, concept_res)
                return enforce_single_question(concept_res)

        # 11c. Zero-Cost Embedded Local SLM & Offline Edge Reasoning
        from core.local_neural_slm import local_neural_slm
        slm_res = local_neural_slm.reason(clean_prompt, context=full_context)
        if slm_res:
            memory.log_interaction("JARVIS (Local Neural SLM)", slm_res)
            vector_memory.index_interaction(clean_prompt, slm_res)
            return enforce_single_question(slm_res)

        # 12. Check if prompt can be fulfilled by local butler intelligence
        handled, local_res = local_intelligence.evaluate_and_execute(clean_prompt)
        if handled:
            memory.log_interaction("JARVIS (Local Core)", local_res)
            vector_memory.index_interaction(clean_prompt, local_res)
            return enforce_single_question(local_res)

        # 13. Problem Healing & Simple English Resolution
        from core.problem_healer import problem_healer
        rectified, explanation = problem_healer.handle_problem(
            problem_type="network",
            details="Unable to connect to online neural networks for query.",
            notify_if_unrectified=True
        )

        if rectified:
            retry_res = online_intelligence.query(redacted_prompt, context=full_context)
            if retry_res:
                memory.log_interaction("JARVIS (Online Core)", retry_res)
                vector_memory.index_interaction(clean_prompt, retry_res)
                return enforce_single_question(retry_res)
            repaired_msg = "I have restored our network connection, sir. How may I be of service?"
            return enforce_single_question(repaired_msg)

        offline_msg = explanation if explanation else "I cannot connect to the internet right now, sir. Please check your network connection."
        memory.log_interaction("JARVIS (Offline Notice)", offline_msg)
        vector_memory.index_interaction(clean_prompt, offline_msg)
        return enforce_single_question(offline_msg)

# Global singleton
brain = JarvisBrain()
