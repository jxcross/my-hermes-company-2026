## functions

- name: lint
  signature: lint(name_or_path)
- name: all_templates
  signature: all_templates()
- name: main
  signature: main()
- name: log
  signature: log(msg)
- name: hermes_prefix
  signature: hermes_prefix()
- name: ensure_board
  signature: ensure_board(slug, mission, dry)
- name: kan
  signature: kan(args, check)
- name: kan_or_abort
  signature: kan_or_abort(args, what)
- name: create_task
  signature: create_task(title, assignee, workspace, body, parents)
- name: load_template
  signature: load_template(name_or_path)
- name: stage_by_id
  signature: stage_by_id(stages, sid)
- name: registered_profiles
  signature: registered_profiles()
- name: missing_profiles
  signature: missing_profiles(tpl)
- name: check_invariants
  signature: check_invariants(tpl)
- name: resolve
  signature: resolve(tpl, mid)
- name: is_gated_downstream
  signature: is_gated_downstream(stage, stages)
- name: parallel_spec
  signature: parallel_spec(stage)
- name: normalize_batch_size
  signature: normalize_batch_size(v)
- name: batch_plan
  signature: batch_plan(count, batch_size)
- name: fanout_label
  signature: fanout_label(stage)
- name: batch_lines
  signature: batch_lines(p)
- name: fanout_body
  signature: fanout_body(stage, base_body)
- name: render_mermaid
  signature: render_mermaid(tpl, mid)
- name: render_ascii
  signature: render_ascii(tpl, mid)
- name: instantiate
  signature: instantiate(tpl, mid, topic, dry, ids)
- name: build_pipeline_json
  signature: build_pipeline_json(tpl, mid, topic, ids)
- name: write_pipeline_json
  signature: write_pipeline_json(mid, pipeline)
- name: main
  signature: main()
- name: verdict_of
  signature: verdict_of(spread, gain, n, completed)
- name: chat
  signature: chat(model, prompt, num_predict, timeout)
- name: prompt_for
  signature: prompt_for(i)
- name: probe
  signature: probe(model, n, reps, timeout)
- name: render
  signature: render(res)
- name: main
  signature: main()
- name: tokens
  signature: tokens(text)
- name: load_templates
  signature: load_templates()
- name: template_terms
  signature: template_terms(t)
- name: score
  signature: score(query, t)
- name: rank
  signature: rank(query, tpls)
- name: verdict
  signature: verdict(top)
- name: rebuild_manifest
  signature: rebuild_manifest(tpls)
- name: main
  signature: main()
- name: chat
  signature: chat(model, messages, tools, timeout)
- name: run_agent
  signature: run_agent(model, prompt, tools)
- name: probe_write
  signature: probe_write(model)
- name: probe_verdict
  signature: probe_verdict(model)
- name: measure
  signature: measure(model, reps)
- name: main
  signature: main()
- name: hermes_bin
  signature: hermes_bin()
- name: insights
  signature: insights()
- name: log_files
  signature: log_files()
- name: scan_limits
  signature: scan_limits(paths)
- name: ollama_tags
  signature: ollama_tags(url)
- name: ollama_ps
  signature: ollama_ps(url)
- name: check_runtime
  signature: check_runtime(url)
- name: check_local
  signature: check_local(backend, url)
- name: main_local
  signature: main_local(args, backend)
- name: main
  signature: main()
- name: profile_of_tier
  signature: profile_of_tier()
- name: targets
  signature: targets(repo_root)
- name: find_block
  signature: find_block(lines, name)
- name: find_model_block
  signature: find_model_block(lines)
- name: parse_model_block
  signature: parse_model_block(lines, name)
- name: render_model_block
  signature: render_model_block(backend, model, with_header)
- name: render_extra_block
  signature: render_extra_block(backend, name)
- name: apply_to_file
  signature: apply_to_file(path, backend, model, with_header)
- name: inspect
  signature: inspect(repo_root)
- name: active_backend
  signature: active_backend(repo_root)
- name: modelfile
  signature: modelfile(derived)
- name: cmd_build_models
  signature: cmd_build_models(backend)
- name: backend_models
  signature: backend_models(backend)
- name: cmd_show
  signature: cmd_show(repo_root, as_json)
- name: cmd_apply
  signature: cmd_apply(repo_root, backend, dry_run)
- name: server_env_state
  signature: server_env_state(log_path)
- name: host_env_state
  signature: host_env_state()
- name: cmd_host_setup
  signature: cmd_host_setup(dry_run)
- name: main
  signature: main(argv)
- name: load_template
  signature: load_template(name)
- name: gate_stages
  signature: gate_stages(tpl)
- name: scaffold
  signature: scaffold(mid, tpl)
- name: draft_abs
  signature: draft_abs(base, mid, declared, root)
- name: check
  signature: check(name, verbose)
- name: main
  signature: main()
- name: norm
  signature: norm(draft, mid_token)
- name: template_stage_drafts
  signature: template_stage_drafts(name)
- name: fixture_drafts
  signature: fixture_drafts(harness)
- name: check
  signature: check(harness, tpl_name)
- name: main
  signature: main()
- name: log
  signature: log(msg)
- name: board_scope
  signature: board_scope(slug)
- name: current_board
  signature: current_board()
- name: run
  signature: run(args, check)
- name: kanban_json
  signature: kanban_json(args)
- name: active_boards
  signature: active_boards()
- name: board_of
  signature: board_of(mission)
- name: notify
  signature: notify(text, dry)
- name: load_state
  signature: load_state()
- name: save_state
  signature: save_state(state)
- name: verdict_texts
  signature: verdict_texts(show)
- name: verdict_signal_present
  signature: verdict_signal_present(show)
- name: parse_verdict
  signature: parse_verdict(show, assignee)
- name: mission_of
  signature: mission_of(title)
- name: stage_tag
  signature: stage_tag(title)
- name: verifier_profiles
  signature: verifier_profiles()
- name: load_pipeline
  signature: load_pipeline(mission)
- name: objective_verdict
  signature: objective_verdict(vid, title)
- name: task_assignee
  signature: task_assignee(task_id)
- name: task_status
  signature: task_status(task_id)
- name: revision_round_count
  signature: revision_round_count(mission, tag)
- name: handle_pass
  signature: handle_pass(vid, title, children, dry)
- name: handle_fail
  signature: handle_fail(vid, title, assignee, parents, children, instr, dry)
- name: verifier_instruction
  signature: verifier_instruction(show, assignee)
- name: classify_children
  signature: classify_children(children, status_of)
- name: poll_once
  signature: poll_once(processed, dry)
- name: slack_api
  signature: slack_api(method, params, post)
- name: parse_approval
  signature: parse_approval(text)
- name: pending_sam_gates
  signature: pending_sam_gates(pipelines)
- name: all_upstream_done
  signature: all_upstream_done(upstream, board)
- name: load_all_pipelines
  signature: load_all_pipelines()
- name: approval_artifact_of
  signature: approval_artifact_of(g, pl)
- name: gate_summary
  signature: gate_summary(g, pl)
- name: artifact_inspection
  signature: artifact_inspection(root, max_files)
- name: resolve_approval_target
  signature: resolve_approval_target(explicit_id, gates)
- name: seed_approval_baseline
  signature: seed_approval_baseline(state)
- name: approval_poll
  signature: approval_poll(state, dry)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: scope_formats
  signature: scope_formats(root)
- name: count_words
  signature: count_words(text)
- name: recommended_option
  signature: recommended_option(options_path)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: scope_value
  signature: scope_value(root, key)
- name: chars_with_url_rule
  signature: chars_with_url_rule(text)
- name: count_words
  signature: count_words(text)
- name: check_twitter
  signature: check_twitter(text, spec)
- name: check_medium
  signature: check_medium(text, spec)
- name: check_readme
  signature: check_readme(text, spec)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: parse_block
  signature: parse_block(text, block_re)
- name: known_source_ids
  signature: known_source_ids(path)
- name: content_lines
  signature: content_lines(text)
- name: bracket_issue
  signature: bracket_issue(lines)
- name: count_nodes
  signature: count_nodes(dtype, lines)
- name: lint_mermaid
  signature: lint_mermaid(text, valid, max_nodes, min_lines)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: parse_cves
  signature: parse_cves(block)
- name: int_field
  signature: int_field(text, key)
- name: find_draft
  signature: find_draft(draft)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: norm
  signature: norm(name)
- name: parse_canonical
  signature: parse_canonical(path)
- name: split_spec
  signature: split_spec(token)
- name: parse_pip
  signature: parse_pip(path)
- name: parse_conda
  signature: parse_conda(path)
- name: parse_docker
  signature: parse_docker(path, pip_pkgs)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path, key)
- name: mission_root
  signature: mission_root(draft)
- name: scope
  signature: scope(root)
- name: parse_visuals
  signature: parse_visuals(path)
- name: md_files
  signature: md_files(root, rels)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: scope_value
  signature: scope_value(root, key)
- name: parse_block
  signature: parse_block(path, name)
- name: id_list
  signature: id_list(raw)
- name: mentions
  signature: mentions(text, token)
- name: gantt_tasks
  signature: gantt_tasks(text)
- name: source_ids
  signature: source_ids(path)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: scope_value
  signature: scope_value(root, key)
- name: count_words
  signature: count_words(text)
- name: read
  signature: read(path)
- name: section_path
  signature: section_path(sec_dir, name, aliases)
- name: gantt_tasks
  signature: gantt_tasks(text)
- name: ascii_ratio
  signature: ascii_ratio(text)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: parse_stakeholders
  signature: parse_stakeholders(context_path)
- name: id_ref_re
  signature: id_ref_re(sid)
- name: covered_in
  signature: covered_in(s, text, min_name_len)
- name: format_files
  signature: format_files(draft)
- name: mission_root
  signature: mission_root(draft)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path, key)
- name: mission_root
  signature: mission_root(draft)
- name: find
  signature: find(root)
- name: declared_vars
  signature: declared_vars(root)
- name: field
  signature: field(text, key)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: slug
  signature: slug(s)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: block
  signature: block(text, name)
- name: defined_los
  signature: defined_los(objectives_text)
- name: entries_with_los
  signature: entries_with_los(blk)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: body_of
  signature: body_of(text)
- name: count_hype
  signature: count_hype(text, pats)
- name: posts_of
  signature: posts_of(text)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: normalize
  signature: normalize(text)
- name: verbatim_sections
  signature: verbatim_sections(text)
- name: review_files
  signature: review_files(d)
- name: numbered_items
  signature: numbered_items(text)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: find_spec_doc
  signature: find_spec_doc(start_dir)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: field
  signature: field(text, key)
- name: is_unpinned
  signature: is_unpinned(value, unpinned)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: claims_section
  signature: claims_section(text)
- name: spec_body
  signature: spec_body(text)
- name: claim_blocks
  signature: claim_blocks(claims_text)
- name: elements_of
  signature: elements_of(body)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: scope_value
  signature: scope_value(root, key)
- name: count_words
  signature: count_words(text)
- name: parse_criteria
  signature: parse_criteria(path)
- name: match_program
  signature: match_program(program, rules)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: field
  signature: field(text, key)
- name: read
  signature: read(path)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: scope_field
  signature: scope_field(root, key)
- name: parse_declared
  signature: parse_declared(path)
- name: py_files
  signature: py_files(root, exclude)
- name: is_public
  signature: is_public(name)
- name: extract_python
  signature: extract_python(root, exclude)
- name: sig_params
  signature: sig_params(signature)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: frontmatter
  signature: frontmatter(path)
- name: normalize
  signature: normalize(text)
- name: strip_tags
  signature: strip_tags(text, tag_re)
- name: paragraphs
  signature: paragraphs(text)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: classify_text
  signature: classify_text(text)
- name: declared_in
  signature: declared_in(path)
- name: compatibility
  signature: compatibility(source, intent, extra)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: scope_level
  signature: scope_level(root)
- name: normalize
  signature: normalize(raw)
- name: parse_objectives
  signature: parse_objectives(text)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: is_redacted
  signature: is_redacted(raw)
- name: scan
  signature: scan(text, kinds)
- name: files_of
  signature: files_of(draft, exts)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: parse_symbols
  signature: parse_symbols(path)
- name: documented_entries
  signature: documented_entries(api_text, min_body)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: gold_count
  signature: gold_count(root)
- name: raw_path_for
  signature: raw_path_for(root, run_id)
- name: count_lines
  signature: count_lines(path)
- name: scalars
  signature: scalars(d, prefix)
- name: check_model_pin
  signature: check_model_pin(value, field, run_id, vague)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: find_eval_set
  signature: find_eval_set(draft)
- name: load_items
  signature: load_items(path)
- name: load_chunk_ids
  signature: load_chunk_ids(path)
- name: norm_difficulty
  signature: norm_difficulty(v)
- name: norm_question
  signature: norm_question(q)
- name: gold_contexts
  signature: gold_contexts(item)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: declared_count
  signature: declared_count(root)
- name: parse_runs_block
  signature: parse_runs_block(root)
- name: schema_of
  signature: schema_of(path)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: response_id
  signature: response_id(path)
- name: body_words
  signature: body_words(path)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: scope_field
  signature: scope_field(root, key)
- name: parse_items
  signature: parse_items(block, id_field)
- name: as_list
  signature: as_list(v)
- name: git
  signature: git(repo)
- name: check_plan
  signature: check_plan(steps, prefix, require_rollback, allow_overlap)
- name: check_executed
  signature: check_executed(steps, executed, repo, prefix, verify_git)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: parse_entries
  signature: parse_entries(text)
- name: find_draft
  signature: find_draft(draft)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: scope
  signature: scope(root)
- name: parse_block
  signature: parse_block(text, block_re)
- name: words
  signature: words(s)
- name: note_body
  signature: note_body(text)
- name: is_placeholder
  signature: is_placeholder(s, terms)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: scope_jurisdictions
  signature: scope_jurisdictions(mission_root)
- name: app_files
  signature: app_files(draft)
- name: jurisdiction_of
  signature: jurisdiction_of(path, known)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: scope_field
  signature: scope_field(root, key)
- name: strip_frontmatter
  signature: strip_frontmatter(text)
- name: clause_patterns
  signature: clause_patterns(label)
- name: clause_present
  signature: clause_present(label, aliases, body)
- name: doc_files
  signature: doc_files(draft)
- name: mission_root
  signature: mission_root(draft)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path, key)
- name: mission_root
  signature: mission_root(draft)
- name: parse_schema
  signature: parse_schema(path)
- name: read_shape
  signature: read_shape(path)
- name: int_field
  signature: int_field(text, key)
- name: format_dirs
  signature: format_dirs(base)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: find_design
  signature: find_design(root)
- name: parse_systems
  signature: parse_systems(block)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: norm
  signature: norm(s)
- name: law_name_before
  signature: law_name_before(text, pos, whitelist)
- name: check_doc
  signature: check_doc(path, whitelist, max_article)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path, key)
- name: mission_root
  signature: mission_root(draft)
- name: check_publication_scope
  signature: check_publication_scope(root, pub)
- name: is_placeholder
  signature: is_placeholder(raw)
- name: scan_pii
  signature: scan_pii(text, kinds, allow_placeholder)
- name: doc_files
  signature: doc_files(draft)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path, key)
- name: mission_root
  signature: mission_root(draft)
- name: luhn_valid
  signature: luhn_valid(s)
- name: scan_text
  signature: scan_text(text, names)
- name: strings_of
  signature: strings_of(path)
- name: walk_json
  signature: walk_json(obj)
- name: data_files
  signature: data_files(root, exts, unreadable)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: parse_claims
  signature: parse_claims(path)
- name: source_text
  signature: source_text(root, rel)
- name: cited_ids
  signature: cited_ids(text)
- name: segments
  signature: segments(text)
- name: citations_at
  signature: citations_at(segs, pos)
- name: norm_num
  signature: norm_num(s)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: scope_level
  signature: scope_level(root)
- name: images
  signature: images(text)
- name: sentences
  signature: sentences(text)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: find_doc
  signature: find_doc(draft, bundle_dir)
- name: sections_of
  signature: sections_of(text)
- name: body_chars
  signature: body_chars(body)
- name: match_section
  signature: match_section(secs, aliases)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: load_sources
  signature: load_sources(path)
- name: selected_ids
  signature: selected_ids(sources)
- name: strip_frontmatter
  signature: strip_frontmatter(text)
- name: word_count
  signature: word_count(text)
- name: evidence_bullets
  signature: evidence_bullets(text, min_chars)
- name: find_markers
  signature: find_markers(text, extra)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: scope_field
  signature: scope_field(root, key)
- name: block
  signature: block(text, name)
- name: weeks
  signature: weeks(text)
- name: los
  signature: los(text)
- name: read_all
  signature: read_all(path)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: parse_systems
  signature: parse_systems(root)
- name: per_item_values
  signature: per_item_values(metrics, metric)
- name: system_item_means
  signature: system_item_means(root, system, metric)
- name: eval_set_size
  signature: eval_set_size(root)
- name: cohens_d_paired
  signature: cohens_d_paired(diffs)
- name: paired_bootstrap_ci
  signature: paired_bootstrap_ci(diffs, n_samples, alpha, seed)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: parse_findings
  signature: parse_findings(block)
- name: int_field
  signature: int_field(text, key)
- name: find_draft
  signature: find_draft(draft)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: parse_counts
  signature: parse_counts(block)
- name: parse_reasons
  signature: parse_reasons(block)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: find
  signature: find(root)
- name: parse_key_results
  signature: parse_key_results(block)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: field
  signature: field(text, key)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: load_candidates
  signature: load_candidates(path)
- name: scope_monitor_id
  signature: scope_monitor_id(mission_root)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: scope_value
  signature: scope_value(root, key)
- name: parse_amount
  signature: parse_amount(cell)
- name: parse_resources
  signature: parse_resources(path)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: load_sources
  signature: load_sources(path)
- name: included_sources
  signature: included_sources(sources, policy)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: normalize_grade
  signature: normalize_grade(raw)
- name: parse_grades
  signature: parse_grades(evidence_path)
- name: paragraph_bounds
  signature: paragraph_bounds(text, pos)
- name: caveat_scope
  signature: caveat_scope(text, start, end)
- name: has_caveat
  signature: has_caveat(scope, terms)
- name: recommendation_scope
  signature: recommendation_scope(text, headings)
- name: format_files
  signature: format_files(draft)
- name: mission_root
  signature: mission_root(draft)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: normalize
  signature: normalize(t)
- name: check_item
  signature: check_item(item, text_norm)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: file_sha256
  signature: file_sha256(path)
- name: hash_directory
  signature: hash_directory(root, exclude)
- name: parse_doe
  signature: parse_doe(root)
- name: num_eq
  signature: num_eq(a, b)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: find_dir
  signature: find_dir(draft)
- name: sections_of
  signature: sections_of(text)
- name: body_chars
  signature: body_chars(body)
- name: match_section
  signature: match_section(secs, aliases)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: words
  signature: words(s)
- name: body_of
  signature: body_of(text)
- name: count_bullets
  signature: count_bullets(body)
- name: count_visuals
  signature: count_visuals(body)
- name: deck_slide_chunks
  signature: deck_slide_chunks(text)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: mission_root
  signature: mission_root(draft)
- name: split_doc
  signature: split_doc(path)
- name: prose
  signature: prose(body)
- name: words
  signature: words(text)
- name: sentences
  signature: sentences(text)
- name: has_any
  signature: has_any(text, markers)
- name: has_phrase
  signature: has_phrase(text, phrases)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path, key)
- name: load_sources
  signature: load_sources(path)
- name: resolve_year
  signature: resolve_year(policy, abs_key, off_key, default_off, now_year)
- name: included_sources
  signature: included_sources(sources, policy)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: parse_items
  signature: parse_items(text, block, id_field)
- name: read
  signature: read(path)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: load_ids
  signature: load_ids(path)
- name: split_items
  signature: split_items(text)
- name: word_count
  signature: word_count(body)
- name: main
  signature: main()
- name: load_policy
  signature: load_policy(path)
- name: read
  signature: read(path)
- name: find_doc
  signature: find_doc(spec_dir)
- name: ids
  signature: ids(pattern, text)
- name: nongoal_terms
  signature: nongoal_terms(prd, min_len)
- name: main
  signature: main()
- name: norm
  signature: norm(s)
- name: words
  signature: words(s)
- name: as_list
  signature: as_list(v)
- name: load_yaml
  signature: load_yaml(path)
- name: load_candidates
  signature: load_candidates(path)
- name: score_one
  signature: score_one(c, wl)
- name: main
  signature: main()
- name: monitors_root
  signature: monitors_root()
- name: seen_path
  signature: seen_path(monitor_id)
- name: load_seen
  signature: load_seen(monitor_id)
- name: append_seen
  signature: append_seen(monitor_id, ids, date)
- name: today
  signature: today(explicit)
- name: main
  signature: main()
- name: role_monthly
  signature: role_monthly(role, override)
- name: build_table
  signature: build_table(spec)
- name: indirect_label
  signature: indirect_label(rate)
- name: write_md
  signature: write_md(s, out)
- name: write_csv
  signature: write_csv(s, out)
- name: main
  signature: main()
- name: load_sources
  signature: load_sources(path)
- name: escape
  signature: escape(v)
- name: authors_field
  signature: authors_field(v)
- name: to_entry
  signature: to_entry(s)
- name: main
  signature: main()
- name: test_parses_reset_time_and_plan
  signature: test_parses_reset_time_and_plan()
- name: test_no_limit_record_is_not_exhausted
  signature: test_no_limit_record_is_not_exhausted()
- name: test_auth_failure_counts_as_environment_failure_not_limit
  signature: test_auth_failure_counts_as_environment_failure_not_limit()
- name: test_exhaustion_verdict_uses_injected_clock
  signature: test_exhaustion_verdict_uses_injected_clock()
- name: test_latest_record_wins_across_files
  signature: test_latest_record_wins_across_files()
- name: test_main_exit_codes
  signature: test_main_exit_codes(capsys)
- name: test_local_backend_ignores_stale_codex_limit
  signature: test_local_backend_ignores_stale_codex_limit(monkeypatch)
- name: test_local_backend_blocks_when_model_missing
  signature: test_local_backend_blocks_when_model_missing()
- name: test_local_backend_blocks_when_server_unreachable
  signature: test_local_backend_blocks_when_server_unreachable()
- name: test_check_local_accepts_latest_suffix_variants
  signature: test_check_local_accepts_latest_suffix_variants()
- name: test_local_probe_never_calls_an_llm
  signature: test_local_probe_never_calls_an_llm()
- name: test_norm_env_treats_notation_differences_as_equal
  signature: test_norm_env_treats_notation_differences_as_equal()
- name: test_banner_found_even_when_far_from_end_of_a_large_log
  signature: test_banner_found_even_when_far_from_end_of_a_large_log()
- name: test_banner_partial_window_does_not_yield_truncated_values
  signature: test_banner_partial_window_does_not_yield_truncated_values()
- name: test_server_env_state_flags_unapplied_settings
  signature: test_server_env_state_flags_unapplied_settings()
- name: test_server_env_state_passes_when_applied
  signature: test_server_env_state_passes_when_applied()
- name: test_server_env_state_unavailable_does_not_judge
  signature: test_server_env_state_unavailable_does_not_judge()
- name: test_runtime_check_never_blocks_mission_start
  signature: test_runtime_check_never_blocks_mission_start()
- name: test_context_mismatch_is_detected_from_the_server_not_the_config
  signature: test_context_mismatch_is_detected_from_the_server_not_the_config()
- name: test_context_mismatch_ignores_models_outside_the_batch
  signature: test_context_mismatch_ignores_models_outside_the_batch()
- name: test_no_context_mismatch_when_server_matches
  signature: test_no_context_mismatch_when_server_matches()
- name: test_restart_pending_separates_not_set_from_not_applied
  signature: test_restart_pending_separates_not_set_from_not_applied()
- name: test_omitted_var_is_flagged_when_present
  signature: test_omitted_var_is_flagged_when_present()
- name: test_parallel_probe_verdicts_on_real_measurements
  signature: test_parallel_probe_verdicts_on_real_measurements()
- name: test_parallel_probe_rejects_no_gain_even_when_ends_cluster
  signature: test_parallel_probe_rejects_no_gain_even_when_ends_cluster()
- name: test_parallel_probe_incomplete_beats_a_fast_looking_ratio
  signature: test_parallel_probe_incomplete_beats_a_fast_looking_ratio()
- name: test_main_fail_closed_when_no_logs
  signature: test_main_fail_closed_when_no_logs()
- name: test_writer_and_verifier_share_a_model_only_by_explicit_declaration
  signature: test_writer_and_verifier_share_a_model_only_by_explicit_declaration()
- name: test_window_escapes_the_degenerate_compaction_branch
  signature: test_window_escapes_the_degenerate_compaction_branch()
- name: test_compression_threshold_is_written_per_profile
  signature: test_compression_threshold_is_written_per_profile()
- name: test_every_profile_has_exactly_one_tier
  signature: test_every_profile_has_exactly_one_tier()
- name: test_ollama_block_carries_every_required_key
  signature: test_ollama_block_carries_every_required_key()
- name: test_every_ollama_model_is_a_context_pinned_derivative
  signature: test_every_ollama_model_is_a_context_pinned_derivative()
- name: test_modelfile_pins_each_models_own_window
  signature: test_modelfile_pins_each_models_own_window()
- name: test_no_model_is_pinned_above_its_measured_ceiling
  signature: test_no_model_is_pinned_above_its_measured_ceiling()
- name: test_deployed_models_pin_the_same_window_as_the_config
  signature: test_deployed_models_pin_the_same_window_as_the_config()
- name: test_derived_name_carries_its_window
  signature: test_derived_name_carries_its_window()
- name: test_model_names_with_colons_are_quoted
  signature: test_model_names_with_colons_are_quoted()
- name: test_finds_model_block_and_stops_at_next_top_level_key
  signature: test_finds_model_block_and_stops_at_next_top_level_key()
- name: test_parses_values_and_strips_quotes
  signature: test_parses_values_and_strips_quotes()
- name: test_nested_keys_are_not_read_as_top_level
  signature: test_nested_keys_are_not_read_as_top_level()
- name: test_preserves_agent_block_in_source_config
  signature: test_preserves_agent_block_in_source_config()
- name: test_writes_compression_block_and_keeps_other_blocks
  signature: test_writes_compression_block_and_keeps_other_blocks()
- name: test_codex_switch_removes_the_ollama_only_compression_block
  signature: test_codex_switch_removes_the_ollama_only_compression_block()
- name: test_preserves_onboarding_block_written_by_hermes
  signature: test_preserves_onboarding_block_written_by_hermes()
- name: test_preserves_root_config_large_blocks
  signature: test_preserves_root_config_large_blocks()
- name: test_live_file_gets_no_generated_header
  signature: test_live_file_gets_no_generated_header()
- name: test_apply_switches_every_target_and_show_agrees
  signature: test_apply_switches_every_target_and_show_agrees()
- name: test_round_trip_returns_to_original_codex_placement
  signature: test_round_trip_returns_to_original_codex_placement()
- name: test_detects_mixed_state
  signature: test_detects_mixed_state()
- name: test_inconsistent_model_within_one_backend_is_reported
  signature: test_inconsistent_model_within_one_backend_is_reported()
- name: test_missing_hermes_home_does_not_fail
  signature: test_missing_hermes_home_does_not_fail()
- name: test_inserts_block_when_config_has_none
  signature: test_inserts_block_when_config_has_none()
- name: test_second_apply_is_a_no_op
  signature: test_second_apply_is_a_no_op()
- name: test_dry_run_changes_nothing
  signature: test_dry_run_changes_nothing()
- name: test_backend_models_helper
  signature: test_backend_models_helper()
- name: test_active_backend_helper_on_real_repo_shape
  signature: test_active_backend_helper_on_real_repo_shape()
- name: test_none_status_child_is_unknown_not_terminal
  signature: test_none_status_child_is_unknown_not_terminal()
- name: test_blocked_child_is_actionable
  signature: test_blocked_child_is_actionable()
- name: test_done_and_archived_children_are_terminal
  signature: test_done_and_archived_children_are_terminal()
- name: test_mixed_children
  signature: test_mixed_children()
- name: test_parse_approval_bare
  signature: test_parse_approval_bare()
- name: test_parse_approval_with_explicit_id
  signature: test_parse_approval_with_explicit_id()
- name: test_parse_approval_english
  signature: test_parse_approval_english()
- name: test_parse_approval_deny_word_is_not_approval
  signature: test_parse_approval_deny_word_is_not_approval()
- name: test_parse_approval_non_approval_text
  signature: test_parse_approval_non_approval_text()
- name: test_resolve_target_explicit_match
  signature: test_resolve_target_explicit_match()
- name: test_resolve_target_explicit_not_a_gate
  signature: test_resolve_target_explicit_not_a_gate()
- name: test_resolve_target_single_bare
  signature: test_resolve_target_single_bare()
- name: test_resolve_target_ambiguous_bare
  signature: test_resolve_target_ambiguous_bare()
- name: test_resolve_target_none_pending
  signature: test_resolve_target_none_pending()
- name: test_extract_section
  signature: test_extract_section()
- name: test_compact_policy
  signature: test_compact_policy()
- name: test_gate_summary_entry_vs_output
  signature: test_gate_summary_entry_vs_output(tmp_path)
- name: test_gate_summary_middle_gate_reads_approval_artifact
  signature: test_gate_summary_middle_gate_reads_approval_artifact()
- name: test_gate_summary_output_gate_finds_draft_md
  signature: test_gate_summary_output_gate_finds_draft_md()
- name: test_compact_completion_policy
  signature: test_compact_completion_policy()
- name: test_approval_artifact_of_missing_returns_none
  signature: test_approval_artifact_of_missing_returns_none()
- name: test_verifier_profiles_reads_template_declaration
  signature: test_verifier_profiles_reads_template_declaration()
- name: test_verifier_profiles_falls_back_when_no_pipeline
  signature: test_verifier_profiles_falls_back_when_no_pipeline()
- name: test_inspection_flags_self_declared_simulation
  signature: test_inspection_flags_self_declared_simulation()
- name: test_inspection_reports_tiny_markdown_files
  signature: test_inspection_reports_tiny_markdown_files()
- name: test_inspection_is_quiet_on_healthy_artifacts
  signature: test_inspection_is_quiet_on_healthy_artifacts()
- name: test_inspection_skips_raw_and_private_directories
  signature: test_inspection_skips_raw_and_private_directories()
- name: test_inspection_returns_empty_for_missing_dir
  signature: test_inspection_returns_empty_for_missing_dir()
- name: test_board_flag_precedes_the_subcommand
  signature: test_board_flag_precedes_the_subcommand()
- name: test_default_board_adds_no_flag
  signature: test_default_board_adds_no_flag()
- name: test_board_scope_restores_previous_scope
  signature: test_board_scope_restores_previous_scope()
- name: test_legacy_pipeline_without_board_falls_back_to_default
  signature: test_legacy_pipeline_without_board_falls_back_to_default()
- name: test_active_boards_falls_back_loudly_when_listing_fails
  signature: test_active_boards_falls_back_loudly_when_listing_fails()
- name: test_active_boards_skips_archived
  signature: test_active_boards_skips_archived()
- name: top
  signature: top(query)
- name: test_templates_load
  signature: test_templates_load()
- name: test_clear_requests_pick_the_right_archetype
  signature: test_clear_requests_pick_the_right_archetype()
- name: test_unrelated_request_is_not_forced
  signature: test_unrelated_request_is_not_forced()
- name: test_single_specific_keyword_is_enough_signal
  signature: test_single_specific_keyword_is_enough_signal()
- name: test_maturity_is_weighted_and_missing_defaults_to_draft
  signature: test_maturity_is_weighted_and_missing_defaults_to_draft()
- name: test_korean_particles_do_not_break_matching
  signature: test_korean_particles_do_not_break_matching()
- name: test_evidence_is_returned_with_the_score
  signature: test_evidence_is_returned_with_the_score()
- name: test_manifest_rebuild_is_derived_not_handwritten
  signature: test_manifest_rebuild_is_derived_not_handwritten()
- name: test_batch_size_defaults_when_absent
  signature: test_batch_size_defaults_when_absent()
- name: test_batch_size_explicit_wins
  signature: test_batch_size_explicit_wins()
- name: test_batch_size_bad_value_falls_back
  signature: test_batch_size_bad_value_falls_back()
- name: test_batch_size_floor_is_one
  signature: test_batch_size_floor_is_one()
- name: test_legacy_parallel_true_still_works
  signature: test_legacy_parallel_true_still_works()
- name: test_batch_plan_splits_five_into_three_plus_two
  signature: test_batch_plan_splits_five_into_three_plus_two()
- name: test_batch_plan_single_round_when_under_cap
  signature: test_batch_plan_single_round_when_under_cap()
- name: test_batch_plan_empty
  signature: test_batch_plan_empty()
- name: test_body_states_batch_cap_and_rounds
  signature: test_body_states_batch_cap_and_rounds()
- name: test_body_warns_batch_is_rejected_not_queued
  signature: test_body_warns_batch_is_rejected_not_queued()
- name: test_body_no_longer_says_all_at_once
  signature: test_body_no_longer_says_all_at_once()
- name: test_body_single_batch_when_workers_fit
  signature: test_body_single_batch_when_workers_fit()
- name: test_body_per_item_tells_model_to_count_first
  signature: test_body_per_item_tells_model_to_count_first()
- name: test_no_parallel_body_unchanged
  signature: test_no_parallel_body_unchanged()
- name: test_label_shows_batch_and_rounds
  signature: test_label_shows_batch_and_rounds()
- name: test_label_omits_rounds_for_single_batch
  signature: test_label_omits_rounds_for_single_batch()
- name: test_shipped_template_declares_batch_size_on_every_parallel_stage
  signature: test_shipped_template_declares_batch_size_on_every_parallel_stage()
- name: test_gate_overlap_is_rejected
  signature: test_gate_overlap_is_rejected()
- name: test_gate_separated_passes
  signature: test_gate_separated_passes()
- name: test_shipped_templates_have_no_gate_overlap
  signature: test_shipped_templates_have_no_gate_overlap()
- name: test_mid_pipeline_sam_gates_declare_approval_artifact
  signature: test_mid_pipeline_sam_gates_declare_approval_artifact()
- name: test_registered_profiles_reads_profiles_src
  signature: test_registered_profiles_reads_profiles_src()
- name: test_missing_profiles_detects_unknown
  signature: test_missing_profiles_detects_unknown()
- name: test_missing_profiles_dedups_and_keeps_order
  signature: test_missing_profiles_dedups_and_keeps_order()
- name: test_shipped_templates_are_all_runnable
  signature: test_shipped_templates_are_all_runnable()
- name: test_webapp_build_required_profiles_are_registered
  signature: test_webapp_build_required_profiles_are_registered()
- name: test_webapp_build_invariants_pass
  signature: test_webapp_build_invariants_pass()
- name: test_sam_gate_and_fanout_marks_are_cumulative
  signature: test_sam_gate_and_fanout_marks_are_cumulative()
- name: test_policy_brief_double_gate_is_complete
  signature: test_policy_brief_double_gate_is_complete()
- name: test_ungated_stage_is_born_with_parent_not_linked_later
  signature: test_ungated_stage_is_born_with_parent_not_linked_later()
- name: test_gated_stage_is_blocked_before_being_linked
  signature: test_gated_stage_is_blocked_before_being_linked()
- name: test_block_failure_aborts_instead_of_leaving_a_gateless_pipeline
  signature: test_block_failure_aborts_instead_of_leaving_a_gateless_pipeline()
- name: test_board_flag_is_injected_in_prefix_before_subcommand
  signature: test_board_flag_is_injected_in_prefix_before_subcommand()
- name: test_no_board_flag_when_default
  signature: test_no_board_flag_when_default()
- name: test_board_slug_regex_matches_hermes_normalisation
  signature: test_board_slug_regex_matches_hermes_normalisation()
- name: test_pipeline_json_records_the_board
  signature: test_pipeline_json_records_the_board()
- name: test_pipeline_json_board_defaults_to_default
  signature: test_pipeline_json_board_defaults_to_default()
- name: test_counts_parse
  signature: test_counts_parse()
- name: test_counts_parse_rejects_non_integer
  signature: test_counts_parse_rejects_non_integer()
- name: test_reasons_parse_sums
  signature: test_reasons_parse_sums()
- name: test_reasons_parse_skips_countless_lines
  signature: test_reasons_parse_skips_countless_lines()
- name: test_bibkey_counting
  signature: test_bibkey_counting()
- name: test_checklist_has_27_items
  signature: test_checklist_has_27_items()
- name: test_checklist_no_is_not_rescued_by_section_hint
  signature: test_checklist_no_is_not_rescued_by_section_hint()
- name: test_checklist_yes_needs_keyword_and_hint
  signature: test_checklist_yes_needs_keyword_and_hint()
- name: test_checklist_korean_keywords_match
  signature: test_checklist_korean_keywords_match()
- name: test_ids_normalize_zero_padding
  signature: test_ids_normalize_zero_padding()
- name: test_scenario_ids_extracted
  signature: test_scenario_ids_extracted()
- name: test_nongoal_terms_from_prd
  signature: test_nongoal_terms_from_prd()
- name: test_nongoal_terms_absent_section
  signature: test_nongoal_terms_absent_section()
- name: test_checkbox_regexes
  signature: test_checkbox_regexes()
- name: test_pass_words_cover_common_spellings
  signature: test_pass_words_cover_common_spellings()
- name: test_digest_splits_items_by_id
  signature: test_digest_splits_items_by_id()
- name: test_digest_word_count_excludes_action_line
  signature: test_digest_word_count_excludes_action_line()
- name: test_digest_action_label_captured_even_if_invalid
  signature: test_digest_action_label_captured_even_if_invalid()
- name: test_digest_no_items_when_format_ignored
  signature: test_digest_no_items_when_format_ignored()
- name: test_digest_default_actions
  signature: test_digest_default_actions()
- name: test_id_format_requires_source_prefix
  signature: test_id_format_requires_source_prefix()
- name: test_scope_monitor_id_read_from_frontmatter
  signature: test_scope_monitor_id_read_from_frontmatter()
- name: test_scope_monitor_id_absent_returns_none
  signature: test_scope_monitor_id_absent_returns_none()
- name: test_monitor_state_roundtrip_is_idempotent
  signature: test_monitor_state_roundtrip_is_idempotent()
- name: test_monitor_state_root_is_overridable
  signature: test_monitor_state_root_is_overridable()
- name: test_claims_section_not_truncated_by_h3
  signature: test_claims_section_not_truncated_by_h3()
- name: test_claim_blocks_numbered
  signature: test_claim_blocks_numbered()
- name: test_elements_extract_korean_with_josa
  signature: test_elements_extract_korean_with_josa()
- name: test_elements_reject_verbal_phrases
  signature: test_elements_reject_verbal_phrases()
- name: test_spec_body_joins_two_sections
  signature: test_spec_body_joins_two_sections()
- name: test_dependent_ref_regex
  signature: test_dependent_ref_regex()
- name: test_required_sections_cover_four_jurisdictions
  signature: test_required_sections_cover_four_jurisdictions()
- name: test_jurisdiction_inferred_from_filename
  signature: test_jurisdiction_inferred_from_filename()
- name: test_disclaimer_terms_include_korean_default
  signature: test_disclaimer_terms_include_korean_default()
- name: test_scope_jurisdictions_from_frontmatter
  signature: test_scope_jurisdictions_from_frontmatter()
- name: test_evidence_ref_survives_korean_particles
  signature: test_evidence_ref_survives_korean_particles()
- name: test_evidence_ref_does_not_match_inside_words
  signature: test_evidence_ref_does_not_match_inside_words()
- name: test_grade_aliases_accept_korean
  signature: test_grade_aliases_accept_korean()
- name: test_parse_grades_reads_evidence_block
  signature: test_parse_grades_reads_evidence_block(tmp)
- name: test_recommendation_scope_stops_at_next_heading
  signature: test_recommendation_scope_stops_at_next_heading()
- name: test_caveat_scope_does_not_reach_other_paragraph
  signature: test_caveat_scope_does_not_reach_other_paragraph()
- name: test_stakeholder_id_ref_survives_korean_particles
  signature: test_stakeholder_id_ref_survives_korean_particles()
- name: test_parse_stakeholders_collects_fields
  signature: test_parse_stakeholders_collects_fields()
- name: test_covered_in_matches_by_name_when_id_absent
  signature: test_covered_in_matches_by_name_when_id_absent()
- name: test_option_token_survives_korean_particles
  signature: test_option_token_survives_korean_particles()
- name: test_count_words_strips_frontmatter_and_code
  signature: test_count_words_strips_frontmatter_and_code()
- name: test_default_word_ranges_are_korean_calibrated
  signature: test_default_word_ranges_are_korean_calibrated()
- name: test_scope_formats_from_frontmatter
  signature: test_scope_formats_from_frontmatter()
- name: test_recommended_option_parsed
  signature: test_recommended_option_parsed()
- name: test_clause_pattern_survives_fstring_quantifier
  signature: test_clause_pattern_survives_fstring_quantifier()
- name: test_clause_requires_heading_not_passing_mention
  signature: test_clause_requires_heading_not_passing_mention()
- name: clause_present_none
  signature: clause_present_none(body, label)
- name: test_clause_alias_is_accepted
  signature: test_clause_alias_is_accepted()
- name: test_clause_bold_line_counts_as_heading
  signature: test_clause_bold_line_counts_as_heading()
- name: test_scope_field_reads_doc_types
  signature: test_scope_field_reads_doc_types()
- name: test_law_name_does_not_swallow_preceding_sentence
  signature: test_law_name_does_not_swallow_preceding_sentence()
- name: test_law_name_prefers_bracketed_form
  signature: test_law_name_prefers_bracketed_form()
- name: test_law_name_longest_whitelist_suffix
  signature: test_law_name_longest_whitelist_suffix()
- name: test_internal_article_reference_is_not_a_law_citation
  signature: test_internal_article_reference_is_not_a_law_citation()
- name: test_article_regex_captures_missing_je
  signature: test_article_regex_captures_missing_je()
- name: test_placeholder_is_not_treated_as_pii
  signature: test_placeholder_is_not_treated_as_pii()
- name: test_resident_registration_number_is_blocked
  signature: test_resident_registration_number_is_blocked()
- name: test_business_number_blocked_but_placeholder_passes
  signature: test_business_number_blocked_but_placeholder_passes()
- name: test_disclaimer_terms_include_lawyer_review
  signature: test_disclaimer_terms_include_lawyer_review()
- name: test_extract_python_skips_private_symbols
  signature: test_extract_python_skips_private_symbols()
- name: test_extract_python_collects_methods_qualified
  signature: test_extract_python_collects_methods_qualified()
- name: test_sig_params_ignores_defaults_and_hints
  signature: test_sig_params_ignores_defaults_and_hints()
- name: test_sig_params_handles_nested_commas
  signature: test_sig_params_handles_nested_commas()
- name: test_parse_declared_binds_signature_to_its_entry
  signature: test_parse_declared_binds_signature_to_its_entry()
- name: test_substring_brush_is_not_documentation
  signature: test_substring_brush_is_not_documentation()
- name: test_documented_entry_requires_body
  signature: test_documented_entry_requires_body()
- name: test_documented_entry_name_strips_signature
  signature: test_documented_entry_name_strips_signature()
- name: test_slug_follows_github_rules
  signature: test_slug_follows_github_rules()
- name: test_link_regex_ignores_images
  signature: test_link_regex_ignores_images()
- name: test_lo_ref_survives_korean_particles
  signature: test_lo_ref_survives_korean_particles()
- name: test_only_declared_los_field_counts
  signature: test_only_declared_los_field_counts()
- name: test_entries_split_per_item
  signature: test_entries_split_per_item()
- name: test_defined_los_from_objectives_block
  signature: test_defined_los_from_objectives_block()
- name: test_bloom_korean_aliases
  signature: test_bloom_korean_aliases()
- name: test_bloom_parse_marks_undeclared
  signature: test_bloom_parse_marks_undeclared()
- name: test_bloom_default_policy_separates_warn_and_fail
  signature: test_bloom_default_policy_separates_warn_and_fail()
- name: test_week_regex_reads_korean_and_field_forms
  signature: test_week_regex_reads_korean_and_field_forms()
- name: test_weight_field_parsed_for_sum
  signature: test_weight_field_parsed_for_sum()
- name: test_course_lo_regex_korean_safe
  signature: test_course_lo_regex_korean_safe()
- name: test_bullets_are_separate_sentences
  signature: test_bullets_are_separate_sentences()
- name: test_image_without_alt_is_flagged
  signature: test_image_without_alt_is_flagged()
- name: test_korean_image_hint_alt_recognized
  signature: test_korean_image_hint_alt_recognized()
- name: test_headings_are_not_counted_as_sentences
  signature: test_headings_are_not_counted_as_sentences()
- name: test_missing_commit_message_is_failed_not_skipped
  signature: test_missing_commit_message_is_failed_not_skipped()
- name: test_file_overlap_between_steps_is_failed
  signature: test_file_overlap_between_steps_is_failed()
- name: test_missing_rollback_is_failed
  signature: test_missing_rollback_is_failed()
- name: test_as_list_parses_inline_yaml_list
  signature: test_as_list_parses_inline_yaml_list()
- name: test_field_returns_none_when_absent
  signature: test_field_returns_none_when_absent()
- name: test_field_requires_whole_line_integer
  signature: test_field_requires_whole_line_integer()
- name: test_accept_only_exact_yes
  signature: test_accept_only_exact_yes()
- name: test_parse_items_binds_fields_to_entry
  signature: test_parse_items_binds_fields_to_entry()
- name: test_fingerprint_block_parsed_from_baseline
  signature: test_fingerprint_block_parsed_from_baseline()
- name: test_owasp_requires_structured_entry_not_bare_mention
  signature: test_owasp_requires_structured_entry_not_bare_mention()
- name: test_owasp_entry_fields_bound
  signature: test_owasp_entry_fields_bound()
- name: test_owasp_ids_normalized_uppercase
  signature: test_owasp_ids_normalized_uppercase()
- name: test_cve_scan_evidence_fields
  signature: test_cve_scan_evidence_fields()
- name: test_cve_items_keep_severity_and_remediation
  signature: test_cve_items_keep_severity_and_remediation()
- name: test_findings_parsed_with_all_fields
  signature: test_findings_parsed_with_all_fields()
- name: test_declared_count_field_is_none_when_absent
  signature: test_declared_count_field_is_none_when_absent()
- name: test_default_caps_are_unlimited
  signature: test_default_caps_are_unlimited()
- name: test_masked_secret_is_allowed
  signature: test_masked_secret_is_allowed()
- name: test_real_aws_key_is_blocked
  signature: test_real_aws_key_is_blocked()
- name: test_private_key_block_is_blocked
  signature: test_private_key_block_is_blocked()
- name: test_private_dir_excluded_from_scan
  signature: test_private_dir_excluded_from_scan()
- name: test_disclaimer_terms_mention_not_formal_audit
  signature: test_disclaimer_terms_mention_not_formal_audit()
- name: test_scan_extensions_default_stays_md_only
  signature: test_scan_extensions_default_stays_md_only()
- name: test_difficulty_aliases_accept_korean
  signature: test_difficulty_aliases_accept_korean()
- name: test_question_normalization_catches_reworded_duplicate
  signature: test_question_normalization_catches_reworded_duplicate()
- name: test_gold_context_accepts_str_and_list
  signature: test_gold_context_accepts_str_and_list()
- name: test_zero_variance_effect_size_is_not_infinite
  signature: test_zero_variance_effect_size_is_not_infinite()
- name: test_metric_alias_and_at_k_extraction
  signature: test_metric_alias_and_at_k_extraction()
- name: test_roles_parsed_from_systems_block
  signature: test_roles_parsed_from_systems_block()
- name: test_documented_default_embedding_is_not_rejected
  signature: test_documented_default_embedding_is_not_rejected()
- name: test_unpinned_alias_is_rejected
  signature: test_unpinned_alias_is_rejected()
- name: test_scalars_flattens_nested_metrics
  signature: test_scalars_flattens_nested_metrics()
- name: test_run_name_regex_splits_system_and_seed
  signature: test_run_name_regex_splits_system_and_seed()
- name: test_plain_long_number_is_not_a_phone
  signature: test_plain_long_number_is_not_a_phone()
- name: test_real_korean_phone_is_detected
  signature: test_real_korean_phone_is_detected()
- name: test_luhn_uses_the_match_not_a_fixed_window
  signature: test_luhn_uses_the_match_not_a_fixed_window()
- name: test_masked_values_are_allowed
  signature: test_masked_values_are_allowed()
- name: test_ssn_kr_accepts_spaces_around_hyphen
  signature: test_ssn_kr_accepts_spaces_around_hyphen()
- name: test_walk_json_reaches_nested_strings
  signature: test_walk_json_reaches_nested_strings()
- name: test_restrictive_clause_beats_permissive_header
  signature: test_restrictive_clause_beats_permissive_header()
- name: test_unidentifiable_license_is_red
  signature: test_unidentifiable_license_is_red()
- name: test_unknown_compatibility_is_not_compatible
  signature: test_unknown_compatibility_is_not_compatible()
- name: test_extra_compatible_widens_the_conservative_matrix
  signature: test_extra_compatible_widens_the_conservative_matrix()
- name: test_schema_accepts_both_columns_and_json_schema_shapes
  signature: test_schema_accepts_both_columns_and_json_schema_shapes()
- name: test_row_count_field_accepts_thousands_separator
  signature: test_row_count_field_accepts_thousands_separator()
- name: test_body_chars_ignores_markdown_decoration
  signature: test_body_chars_ignores_markdown_decoration()
- name: test_section_alias_matches_korean_heading
  signature: test_section_alias_matches_korean_heading()
- name: test_declared_metric_count_is_compared_with_parsed
  signature: test_declared_metric_count_is_compared_with_parsed()
- name: test_run_status_regex_reads_the_report
  signature: test_run_status_regex_reads_the_report()
- name: test_pin_is_extracted_only_from_exact_equality
  signature: test_pin_is_extracted_only_from_exact_equality()
- name: test_package_name_normalization
  signature: test_package_name_normalization()
- name: test_dockerfile_mention_is_not_installation
  signature: test_dockerfile_mention_is_not_installation()
- name: test_field_reader_handles_quotes
  signature: test_field_reader_handles_quotes()
- name: test_success_words_exclude_failure
  signature: test_success_words_exclude_failure()
- name: test_document_title_does_not_shadow_a_section
  signature: test_document_title_does_not_shadow_a_section()
- name: test_body_chars_excludes_code_fences
  signature: test_body_chars_excludes_code_fences()
- name: test_command_file_tokens_extracted
  signature: test_command_file_tokens_extracted()
- name: test_hash_directory_matches_original_algorithm
  signature: test_hash_directory_matches_original_algorithm()
- name: test_hash_excludes_volatile_files
  signature: test_hash_excludes_volatile_files()
- name: test_design_point_comparison_is_numeric
  signature: test_design_point_comparison_is_numeric()
- name: test_unpinned_tags_rejected
  signature: test_unpinned_tags_rejected()
- name: test_token_value_detected_but_env_var_name_allowed
  signature: test_token_value_detected_but_env_var_name_allowed()
- name: test_declared_count_fixes_the_denominator
  signature: test_declared_count_fixes_the_denominator()
- name: test_output_schema_is_key_set
  signature: test_output_schema_is_key_set()
- name: test_declared_independent_vars_parsed
  signature: test_declared_independent_vars_parsed()
- name: test_csv_reference_extraction
  signature: test_csv_reference_extraction()
- name: test_caveat_terms_cover_korean_and_english
  signature: test_caveat_terms_cover_korean_and_english()
- name: test_systems_block_parses_change_field
  signature: test_systems_block_parses_change_field()
- name: test_gantt_tasks_ignores_directives
  signature: test_gantt_tasks_ignores_directives()
- name: test_gantt_tasks_empty_chart_is_not_none
  signature: test_gantt_tasks_empty_chart_is_not_none()
- name: test_ascii_ratio_detects_korean_abstract
  signature: test_ascii_ratio_detects_korean_abstract()
- name: test_section_path_accepts_korean_alias
  signature: test_section_path_accepts_korean_alias()
- name: test_parse_amount_rejects_non_numeric
  signature: test_parse_amount_rejects_non_numeric()
- name: test_parse_amount_keeps_negative_visible
  signature: test_parse_amount_keeps_negative_visible()
- name: test_parse_resources_reads_kind_and_missing_block
  signature: test_parse_resources_reads_kind_and_missing_block()
- name: test_match_program_allows_suffix_but_not_unknown
  signature: test_match_program_allows_suffix_but_not_unknown()
- name: test_criteria_block_parsed_with_korean_ids
  signature: test_criteria_block_parsed_with_korean_ids()
- name: test_mentions_survives_korean_particles
  signature: test_mentions_survives_korean_particles()
- name: test_id_list_parses_bracket_and_bare
  signature: test_id_list_parses_bracket_and_bare()
- name: test_normalize_strips_list_markers_on_both_sides
  signature: test_normalize_strips_list_markers_on_both_sides()
- name: test_numbered_items_counts_only_consecutive
  signature: test_numbered_items_counts_only_consecutive()
- name: test_verbatim_sections_split_by_id
  signature: test_verbatim_sections_split_by_id()
- name: test_body_words_excludes_frontmatter_and_changes_block
  signature: test_body_words_excludes_frontmatter_and_changes_block()
- name: test_response_id_prefers_frontmatter_then_filename
  signature: test_response_id_prefers_frontmatter_then_filename()
- name: test_log_line_accepts_bullet_forms
  signature: test_log_line_accepts_bullet_forms()
- name: test_log_line_rejects_empty_description
  signature: test_log_line_rejects_empty_description()
- name: test_strip_tags_removes_change_markers
  signature: test_strip_tags_removes_change_markers()
- name: test_evidence_markers_require_a_locator_not_a_substring
  signature: test_evidence_markers_require_a_locator_not_a_substring()
- name: test_banned_phrase_matching_is_literal
  signature: test_banned_phrase_matching_is_literal()
- name: test_citations_are_scoped_to_the_paragraph
  signature: test_citations_are_scoped_to_the_paragraph()
- name: test_bare_decimal_is_a_number_claim
  signature: test_bare_decimal_is_a_number_claim()
- name: test_cited_ids_returns_unknown_ids_too
  signature: test_cited_ids_returns_unknown_ids_too()
- name: test_norm_num_compares_values_not_substrings
  signature: test_norm_num_compares_values_not_substrings()
- name: test_url_counts_as_23_chars
  signature: test_url_counts_as_23_chars()
- name: test_twitter_numbering_and_cta
  signature: test_twitter_numbering_and_cta()
- name: test_medium_word_range_is_korean_eojeol
  signature: test_medium_word_range_is_korean_eojeol()
- name: test_hype_counting_is_cumulative
  signature: test_hype_counting_is_cumulative()
- name: test_posts_split_by_thread_numbering
  signature: test_posts_split_by_thread_numbering()
- name: test_embargo_compared_to_launch_without_a_clock
  signature: test_embargo_compared_to_launch_without_a_clock()
- name: test_visuals_block_requires_source_and_license
  signature: test_visuals_block_requires_source_and_license()
- name: test_note_placeholder_is_substring_not_equality
  signature: test_note_placeholder_is_substring_not_equality()
- name: test_speaker_block_body_extracted
  signature: test_speaker_block_body_extracted()
- name: test_note_items_recognize_korean_and_english_headings
  signature: test_note_items_recognize_korean_and_english_headings()
- name: test_slides_block_parsed_with_fields
  signature: test_slides_block_parsed_with_fields()
- name: test_body_excludes_speaker_notes_and_frontmatter
  signature: test_body_excludes_speaker_notes_and_frontmatter()
- name: test_visual_counts_image_and_mermaid_placeholder
  signature: test_visual_counts_image_and_mermaid_placeholder()
- name: test_deck_chunks_exclude_deck_frontmatter
  signature: test_deck_chunks_exclude_deck_frontmatter()
- name: test_bracket_check_is_a_stack_not_a_tally
  signature: test_bracket_check_is_a_stack_not_a_tally()
- name: test_er_diagram_cardinality_is_not_a_bracket
  signature: test_er_diagram_cardinality_is_not_a_bracket()
- name: test_quoted_label_parens_are_ignored
  signature: test_quoted_label_parens_are_ignored()
- name: test_node_count_only_for_flowchart
  signature: test_node_count_only_for_flowchart()
- name: test_empty_mermaid_is_not_valid
  signature: test_empty_mermaid_is_not_valid()
- name: test_source_ids_read_evidence_and_figures_blocks
  signature: test_source_ids_read_evidence_and_figures_blocks()
- name: test_file_scope_is_one_segment
  signature: test_file_scope_is_one_segment()
- name: test_rejected_sources_are_not_counted
  signature: test_rejected_sources_are_not_counted()
- name: test_unknown_status_words_are_included_not_dropped
  signature: test_unknown_status_words_are_included_not_dropped()
- name: test_status_exclusion_is_policy_overridable
  signature: test_status_exclusion_is_policy_overridable()
- name: test_substance_passes_a_real_analysis
  signature: test_substance_passes_a_real_analysis()
- name: test_substance_fails_self_declared_simulation
  signature: test_substance_fails_self_declared_simulation()
- name: test_substance_fails_plausible_shard_without_locators
  signature: test_substance_fails_plausible_shard_without_locators()
- name: test_substance_fails_on_empty_shard_dir
  signature: test_substance_fails_on_empty_shard_dir()
- name: test_substance_fails_when_a_selected_source_has_no_shard
  signature: test_substance_fails_when_a_selected_source_has_no_shard()
- name: test_substance_ignores_the_merged_index_file
  signature: test_substance_ignores_the_merged_index_file()
- name: test_substance_locator_check_can_be_disabled_explicitly
  signature: test_substance_locator_check_can_be_disabled_explicitly()
- name: test_substance_upper_bound_catches_runaway_output
  signature: test_substance_upper_bound_catches_runaway_output()
- name: test_bracket_marker_does_not_fire_on_ordinary_simulation_prose
  signature: test_bracket_marker_does_not_fire_on_ordinary_simulation_prose()
- name: test_locator_regex_counts_korean_and_english_forms
  signature: test_locator_regex_counts_korean_and_english_forms()
- name: build
  signature: build()
- name: run
  signature: run(gate, draft)
- name: expect
  signature: expect(label, gate, want, show)
- name: patch
  signature: patch(path, old, new)
- name: w
  signature: w(rel, s)
- name: file_sha256
  signature: file_sha256(path)
- name: hash_dir
  signature: hash_dir(root)
- name: build
  signature: build()
- name: run
  signature: run(gate, draft)
- name: expect
  signature: expect(label, gate, want, show, draft)
- name: patch
  signature: patch(path, old, new)
- name: rehash
  signature: rehash(rid)
- name: w
  signature: w(rel, s)
- name: slide_text
  signature: slide_text(sid, section, title, body, note)
- name: outline_text
  signature: outline_text(plan, n_diagrams, extra_fm)
- name: notes_text
  signature: notes_text(plan)
- name: build
  signature: build(plan, talk, n_diagrams, patent, embargo, basis, ref, launch, mode, scope_extra, bundle)
- name: assemble
  signature: assemble(mermaid, files)
- name: run
  signature: run(gate, draft)
- name: expect
  signature: expect(label, gate, want, show, draft)
- name: patch
  signature: patch(path, old, new, count)
- name: set_policy
  signature: set_policy(section, key, value)
- name: w
  signature: w(rel, s)
- name: response
  signature: response(cid, verdict)
- name: build
  signature: build()
- name: run
  signature: run(gate, draft)
- name: expect
  signature: expect(label, gate, want, show, draft)
- name: patch
  signature: patch(path, old, new, count)
- name: w
  signature: w(rel, s)
- name: build
  signature: build()
- name: run
  signature: run(gate, draft)
- name: expect
  signature: expect(label, gate, want, show, draft)
- name: patch
  signature: patch(path, old, new)
- name: build
  signature: build()
- name: run
  signature: run(gate, draft)
- name: expect
  signature: expect(label, gate, want, show)
- name: patch
  signature: patch(path, old, new)
- name: filler
  signature: filler(n)
- name: build
  signature: build()
- name: run
  signature: run(gate, draft)
- name: expect
  signature: expect(label, gate, want, show)
- name: patch
  signature: patch(path, old, new)
- name: w
  signature: w(rel, s)
- name: twitter
  signature: twitter(n, hype, extra)
- name: medium
  signature: medium(n_para, sent)
- name: build
  signature: build(channels, basis, ref, patent, embargo, mode, launch)
- name: run
  signature: run(gate, draft)
- name: expect
  signature: expect(label, gate, want, show, draft)
- name: patch
  signature: patch(path, old, new, count)
- name: build
  signature: build()
- name: run
  signature: run(gate, draft)
- name: expect
  signature: expect(label, gate, want, show)
- name: patch
  signature: patch(path, old, new)
- name: w
  signature: w(rel, s)
- name: body
  signature: body(n_eojeol)
- name: build
  signature: build(program, years_post_phd, page_limit, n_years, mode)
- name: run
  signature: run(gate, draft, sources)
- name: expect
  signature: expect(label, gate, want, show, draft)
- name: patch
  signature: patch(path, old, new, count)
- name: w
  signature: w(rel, s)
- name: records
  signature: records()
- name: build
  signature: build()
- name: run
  signature: run(gate, draft)
- name: expect
  signature: expect(label, gate, want, show, draft)
- name: patch
  signature: patch(path, old, new)
- name: edit_json
  signature: edit_json(rel, fn)
- name: set_mode
  signature: set_mode(mode)
- name: copy_public
  signature: copy_public()
- name: item_scores
  signature: item_scores(system, i)
- name: w
  signature: w(rel, s)
- name: build
  signature: build()
- name: run
  signature: run(gate, draft)
- name: expect
  signature: expect(label, gate, want, show, draft)
- name: patch
  signature: patch(path, old, new)
- name: rewrite_metrics
  signature: rewrite_metrics(rid, fn)
- name: build
  signature: build()
- name: run
  signature: run(gate, draft)
- name: expect
  signature: expect(label, gate, want, show, draft)
- name: patch
  signature: patch(path, old, new)
- name: draft_drift
  signature: draft_drift()
- name: main
  signature: main()
- name: sh
  signature: sh()
- name: build
  signature: build()
- name: run
  signature: run(gate, draft)
- name: expect
  signature: expect(label, gate, draft, want, show)
- name: patch
  signature: patch(path, old, new)

## classes

- name: InstantiateError

## modules

- lint_template.py:
- instantiate_template.py:
- probe_parallel.py:
- match_template.py:
- probe_protocol.py:
- usage_report.py:
- set_backend.py:
- preflight_gates.py:
- lint_gate_drafts.py:
- gate_keeper.py:
- gates.format_consistency.py:
- gates.channel_format.py:
- gates.diagram_integrity.py:
- gates.cve_remediation.py:
- gates.env_consistency.py:
- gates.release_readiness.py:
- gates.proposal_traceability.py:
- gates.proposal_format.py:
- gates.stakeholder_coverage.py:
- gates.analysis_integrity.py:
- gates.doc_links.py:
- gates.objective_coverage.py:
- gates.outreach_tone.py:
- gates.comment_fidelity.py:
- gates.test_run.py:
- gates.solver_pin.py:
- gates.claim_consistency.py:
- gates.call_alignment.py:
- gates.test_pass_rate.py:
- gates.symbol_truth.py:
- gates.change_consistency.py:
- gates.license_compat.py:
- gates.bloom_distribution.py:
- gates.secret_redaction.py:
- gates.api_coverage.py:
- gates.repro_determinism.py:
- gates.eval_set_quality.py:
- gates.doe_completeness.py:
- gates.comment_coverage.py:
- gates.atomic_commit.py:
- gates.owasp_coverage.py:
- gates.slide_budget.py:
- gates.patent_format.py:
- gates.clause_completeness.py:
- gates.schema_conformance.py:
- gates.run_completeness.py:
- gates.law_citation.py:
- gates.legal_safety.py:
- gates.pii_presence.py:
- gates.claim_provenance.py:
- gates.content_accessibility.py:
- gates.reproduce_doc.py:
- gates.analysis_substance.py:
- gates.course_consistency.py:
- gates.stat_significance.py:
- gates.finding_completeness.py:
- gates.prisma_counts.py:
- gates.result_tolerance.py:
- gates.install_evidence.py:
- gates.seen_dedup.py:
- gates.budget_integrity.py:
- gates.source_balance.py:
- gates.evidence_grade.py:
- gates.prisma_checklist.py:
- gates.bit_exact.py:
- gates.datasheet_completeness.py:
- gates.deck_format.py:
- gates.response_quality.py:
- gates.recency_check.py:
- gates.behavior_diff.py:
- gates.digest_shape.py:
- gates.doc_consistency.py:
- tools.relevance_score.py:
- tools.monitor_state.py:
- tools.budget_build.py:
- tools.bib_export.py:
- tests.test_usage_report.py:
- tests.test_set_backend.py:
- tests.test_gate_keeper.py:
- tests.test_match_template.py:
- tests.test_instantiate_template.py:
- tests.test_gates.py:
- tests.fixtures.legal.py:
- tests.fixtures.sim.py:
- tests.fixtures.slide.py:
- tests.fixtures.rebuttal.py:
- tests.fixtures.repro.py:
- tests.fixtures.lecture.py:
- tests.fixtures.policy.py:
- tests.fixtures.outreach.py:
- tests.fixtures.docs.py:
- tests.fixtures.proposal.py:
- tests.fixtures.dataset.py:
- tests.fixtures.agent.py:
- tests.fixtures.sec.py:
- tests.fixtures.run_all.py:
- tests.fixtures.migrate.py:
